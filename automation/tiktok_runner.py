#!/usr/bin/env python3
import json
import os
import sys
import subprocess
import hashlib
import tempfile
from urllib.parse import urlparse
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QUEUE_PATH = ROOT / "queue.json"
STATE_PATH = ROOT / "state.json"

API_BASE = "https://open.tiktokapis.com"
CREATOR_INFO_URL = API_BASE + "/v2/post/publish/creator_info/query/"
DIRECT_POST_URL = API_BASE + "/v2/post/publish/video/init/"
STATUS_URL = API_BASE + "/v2/post/publish/status/fetch/"

TERMINAL_STATUSES = {"PUBLISH_COMPLETE", "FAILED", "SUBMISSION_UNKNOWN", "PUBLIC_EVIDENCE_MISSING"}
EXPECTED_USERNAME = ".casasemesforo"
MAX_NEW_POSTS_PER_RUN = int(os.getenv("MAX_NEW_POSTS_PER_RUN", "1"))


def utc_now():
    return datetime.now(timezone.utc)


def iso_now():
    return utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value):
    if not value:
        return None
    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def load_json(path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    temp = path.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    temp.replace(path)


def api_post(url, token, body):
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"TikTok HTTP {e.code}; response body omitted") from None
    except urllib.error.URLError as e:
        raise RuntimeError("TikTok network failure; outcome may be unknown") from None

    error = data.get("error") or {}
    if error.get("code") not in (None, "", "ok"):
        raise RuntimeError(
            f"TikTok API error {error.get('code')}"
        )
    return data


def fetch_token_from_broker():
    token_url = os.getenv("TIKTOK_TOKEN_URL", "").strip()
    shared_secret = os.getenv("TIKTOK_RUNNER_SHARED_SECRET", "").strip()

    if not token_url:
        return os.getenv("TIKTOK_ACCESS_TOKEN", "").strip()

    if not shared_secret:
        raise RuntimeError(
            "TIKTOK_TOKEN_URL está configurado, mas TIKTOK_RUNNER_SHARED_SECRET está ausente."
        )

    if urlparse(token_url).scheme != "https":
        raise RuntimeError("Token broker requires HTTPS")
    req = urllib.request.Request(
        token_url,
        method="GET",
        headers={
            "Authorization": f"Bearer {shared_secret}",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Token broker HTTP {e.code}; response body omitted") from None
    except urllib.error.URLError as e:
        raise RuntimeError("Token broker network failure") from None

    token = str(data.get("access_token", "")).strip()
    if not token:
        raise RuntimeError("Token broker did not return an access token")
    return token


def is_tiktok(entry):
    return entry.get("provider", entry.get("publication_provider", "tiktok")) == "tiktok"


def needs_poll(entry):
    if not is_tiktok(entry) or not entry.get("publish_id"):
        return False
    status = entry.get("status")
    return (status not in TERMINAL_STATUSES or
            (status == "PUBLISH_COMPLETE" and entry.get("privacy_level") == "PUBLIC_TO_EVERYONE"
             and not entry.get("publicly_verified")))


def needs_token(queue, state):
    for entry in state.get("posts", {}).values():
        if needs_poll(entry):
            return True

    now = utc_now()
    for post in queue.get("posts", []):
        post_id = str(post.get("id", "")).strip()
        if not is_tiktok(post) or not post_id or post_id in state.get("posts", {}):
            continue
        if post.get("approved") is not True or not post.get("consented_at"):
            continue
        scheduled = parse_time(post.get("scheduled_at"))
        if scheduled and scheduled <= now:
            return True
    return False


def poll_existing(token, state):
    changed = False
    for post_id, entry in list(state.get("posts", {}).items()):
        if not needs_poll(entry):
            continue
        publish_id = entry.get("publish_id")
        if not publish_id:
            continue
        result = api_post(STATUS_URL, token, {"publish_id": publish_id})
        data = result.get("data") or {}
        status = data.get("status") or entry.get("status") or "UNKNOWN"
        entry["status"] = status
        entry["last_checked_at"] = iso_now()
        entry["reconciliation_checks"] = entry.get("reconciliation_checks", 0) + 1
        if data.get("fail_reason"):
            entry["fail_reason"] = data["fail_reason"]
        ids = data.get("publicaly_available_post_id") or data.get("publicly_available_post_id") or []
        if isinstance(ids, (str, int)):
            ids = [ids]
        if ids:
            entry["publicly_available_post_id"] = ids
            entry["public_urls"] = [f"https://www.tiktok.com/@{EXPECTED_USERNAME}/video/{i}" for i in ids if str(i).isdigit()]
        entry["publicly_verified"] = bool(status == "PUBLISH_COMPLETE" and entry.get("public_urls") and entry.get("privacy_level") == "PUBLIC_TO_EVERYONE")
        if status == "PUBLISH_COMPLETE" and entry.get("privacy_level") == "PUBLIC_TO_EVERYONE" and not entry["publicly_verified"] and entry["reconciliation_checks"] >= 48:
            entry["status"] = "PUBLIC_EVIDENCE_MISSING"
            entry["recovery"] = "Check TikTok visibility manually; do not resubmit"
        save_json(STATE_PATH, state)
        changed = True
        print(f"[status] {post_id}: {status}")
    return changed


def get_creator_info(token):
    result = api_post(CREATOR_INFO_URL, token, {})
    return result.get("data") or {}


def validate_post(post, creator_info):
    if not is_tiktok(post):
        raise ValueError("Post assigned to another publishing provider")
    if creator_info.get("creator_username") != EXPECTED_USERNAME:
        raise ValueError("Creator identity mismatch: refusing to publish")
    quality = post.get("quality") or {}
    from visual_library import require_evidence
    require_evidence(post)
    if not quality.get("technical_pass") or not quality.get("editorial_approved"):
        raise ValueError("Technical validation and editorial review are required")
    duration = float(quality.get("duration", 0))
    if not 15 <= duration <= min(28, creator_info.get("max_video_post_duration_sec", 0)):
        raise ValueError("Video duration not allowed by creator info")
    if not post.get("official_posting_consent"):
        raise ValueError("Official per-post controls and consent have not been recorded")
    for name in ("comment", "duet", "stitch"):
        if creator_info.get(name + "_disabled") and not post.get("disable_" + name, True):
            raise ValueError("Interaction not allowed by creator settings: " + name)
    prefix = os.getenv("TIKTOK_VERIFIED_VIDEO_PREFIX", "")
    if not prefix.startswith("https://") or not prefix.endswith("/") or not post.get("video_url", "").startswith(prefix):
        raise ValueError("Video URL is outside an explicitly verified prefix")
    required = ["id", "video_url", "scheduled_at", "privacy_level"]
    missing = [key for key in required if not post.get(key)]
    if missing:
        raise ValueError(f"Post {post.get('id')}: faltando {', '.join(missing)}")

    if post.get("approved") is not True:
        raise ValueError(f"Post {post['id']}: approved precisa ser true")
    if not post.get("consented_at"):
        raise ValueError(f"Post {post['id']}: consented_at é obrigatório")

    video_url = post["video_url"]
    if not video_url.startswith("https://"):
        raise ValueError(f"Post {post['id']}: video_url precisa usar HTTPS")

    options = creator_info.get("privacy_level_options") or []
    if post["privacy_level"] not in options:
        raise ValueError(
            f"Post {post['id']}: privacy_level={post['privacy_level']} não está "
            f"entre as opções atuais da conta: {options}"
        )


def submit_post(token, post, creator_info):
    validate_post(post, creator_info)

    # Confirm hosted bytes match the reviewed artifact before sending them to TikTok.
    from media_quality import validate
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "video.mp4"
        with urllib.request.urlopen(post["video_url"], timeout=30) as response, path.open("wb") as out:
            total = 0
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > 20_000_000:
                    raise ValueError("Hosted media exceeds budget")
                out.write(chunk)
        quality = validate(path)
        if quality["sha256"] != post["quality"]["sha256"]:
            raise ValueError("Hosted video differs from reviewed artifact")

    post_info = {
        "title": post.get("title", ""),
        "privacy_level": post["privacy_level"],
        "disable_duet": bool(post.get("disable_duet", False)),
        "disable_comment": bool(post.get("disable_comment", False)),
        "disable_stitch": bool(post.get("disable_stitch", False)),
    }

    if "brand_organic_toggle" in post:
        post_info["brand_organic_toggle"] = bool(post["brand_organic_toggle"])
    if "is_aigc" in post:
        post_info["is_aigc"] = bool(post["is_aigc"])

    body = {
        "post_info": post_info,
        "source_info": {
            "source": "PULL_FROM_URL",
            "video_url": post["video_url"],
        },
    }

    result = api_post(DIRECT_POST_URL, token, body)
    data = result.get("data") or {}
    publish_id = data.get("publish_id")
    if not publish_id:
        raise RuntimeError("TikTok did not return publish_id; submission outcome unknown")
    return publish_id


def checkpoint(state):
    """Persist intent BEFORE the non-idempotent API call. Fail closed if persistence fails."""
    save_json(STATE_PATH, state)
    if os.getenv("GITHUB_ACTIONS") != "true":
        raise RuntimeError("Publishing is restricted to the durable cloud runner")
    root = ROOT.parent
    for args in (["git", "config", "user.name", "github-actions[bot]"],
                 ["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"],
                 ["git", "add", "automation/state.json"],
                 ["git", "commit", "-m", "Checkpoint TikTok submission state"],
                 ["git", "pull", "--rebase", "origin", "main"],
                 ["git", "push", "origin", "HEAD:main"]):
        subprocess.run(args, cwd=root, check=True, timeout=90, capture_output=True)


def summary(state, blocked, submitted):
    public = sum(bool(p.get("publicly_verified")) for p in state["posts"].values())
    unknown = sum(p.get("status") in ("SUBMISSION_UNKNOWN", "PUBLIC_EVIDENCE_MISSING") for p in state["posts"].values())
    text = f"PUBLIC_VERIFIED_TOTAL={public}; SUBMITTED_THIS_RUN={submitted}; BLOCKED={blocked}; UNKNOWN={unknown}"
    print(text)
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write("## Publication evidence\n\n" + text + "\n\nJob success is not publication evidence.\n")


def main():
    queue = load_json(QUEUE_PATH, {"posts": []})
    state = load_json(STATE_PATH, {"posts": {}})
    state.setdefault("posts", {})
    due = [p for p in queue.get("posts", []) if is_tiktok(p) and p.get("id") not in state["posts"]
           and parse_time(p.get("scheduled_at")) and parse_time(p["scheduled_at"]) <= utc_now()]
    candidates = [p for p in due if p.get("approved") is True and p.get("consented_at")]
    blocked = len(due) - len(candidates)
    if blocked:
        print(f"::warning::{blocked} due videos lack approval; no public publication confirmed")
    pending = any(needs_poll(p) for p in state["posts"].values())
    if not candidates and not pending:
        summary(state, blocked, 0)
        return 2 if blocked or any(p.get("status") in ("SUBMISSION_UNKNOWN", "PUBLIC_EVIDENCE_MISSING") for p in state["posts"].values()) else 0
    submitted = 0
    try:
        token = fetch_token_from_broker()
        if not token:
            raise RuntimeError("No valid TikTok access token available")
        poll_existing(token, state)
        if candidates:
            creator = get_creator_info(token)
            for post in sorted(candidates, key=lambda p: p["scheduled_at"])[:MAX_NEW_POSTS_PER_RUN]:
                validate_post(post, creator)
                from visual_library import require_evidence, history
                require_evidence(post, history({}, state))
                if parse_time(post["scheduled_at"]) < utc_now() - timedelta(hours=2):
                    raise ValueError("Expired TikTok slot; explicitly reschedule before publication")
                fingerprint = post["quality"].get("sha256")
                if not fingerprint or any(p.get("sha256") == fingerprint for p in state["posts"].values()):
                    raise ValueError("Missing fingerprint or duplicate media")
                # No automatic retry of ambiguous non-idempotent submission.
                entry = dict(provider="tiktok", status="SUBMISSION_UNKNOWN", submitted_at=iso_now(), sha256=fingerprint,
                             privacy_level=post["privacy_level"], video_url=post["video_url"],
                             concept=post.get("concept"), script_sha256=post.get("script_sha256"),
                             source_urls=post['quality'].get('source_urls', []),
                             visual_sources=post['quality'].get('visual_sources', []),
                             publicly_verified=False, recovery="Reconcile on TikTok before any resubmission")
                state["posts"][post["id"]] = entry
                checkpoint(state)
                publish_id = submit_post(token, post, creator)
                entry.update(publish_id=publish_id, status="PROCESSING_DOWNLOAD", last_checked_at=iso_now())
                checkpoint(state)
                submitted += 1
    finally:
        save_json(STATE_PATH, state)
        summary(state, blocked, submitted)
    return 2 if blocked else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"::error::{type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
