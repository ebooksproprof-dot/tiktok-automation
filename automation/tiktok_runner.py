#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QUEUE_PATH = ROOT / "queue.json"
STATE_PATH = ROOT / "state.json"

API_BASE = "https://open.tiktokapis.com"
CREATOR_INFO_URL = API_BASE + "/v2/post/publish/creator_info/query/"
DIRECT_POST_URL = API_BASE + "/v2/post/publish/video/init/"
STATUS_URL = API_BASE + "/v2/post/publish/status/fetch/"

TERMINAL_STATUSES = {"PUBLISH_COMPLETE", "FAILED"}
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
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


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
        raise RuntimeError(f"TikTok HTTP {e.code}: {body_text}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Falha de rede ao chamar TikTok: {e}") from e

    error = data.get("error") or {}
    if error.get("code") not in (None, "", "ok"):
        raise RuntimeError(
            f"TikTok API error {error.get('code')}: {error.get('message', '')}"
        )
    return data


def needs_token(queue, state):
    for entry in state.get("posts", {}).values():
        if entry.get("status") not in TERMINAL_STATUSES:
            return True

    now = utc_now()
    for post in queue.get("posts", []):
        post_id = str(post.get("id", "")).strip()
        if not post_id or post_id in state.get("posts", {}):
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
        if entry.get("status") in TERMINAL_STATUSES:
            continue
        publish_id = entry.get("publish_id")
        if not publish_id:
            continue
        result = api_post(STATUS_URL, token, {"publish_id": publish_id})
        data = result.get("data") or {}
        status = data.get("status") or entry.get("status") or "UNKNOWN"
        entry["status"] = status
        entry["last_checked_at"] = iso_now()
        if data.get("fail_reason"):
            entry["fail_reason"] = data["fail_reason"]
        if data.get("publicaly_available_post_id"):
            entry["publicly_available_post_id"] = data["publicaly_available_post_id"]
        changed = True
        print(f"[status] {post_id}: {status}")
    return changed


def get_creator_info(token):
    result = api_post(CREATOR_INFO_URL, token, {})
    return result.get("data") or {}


def validate_post(post, creator_info):
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
        raise RuntimeError(f"TikTok não retornou publish_id: {result}")
    return publish_id


def main():
    queue = load_json(QUEUE_PATH, {"posts": []})
    state = load_json(STATE_PATH, {"posts": {}})
    state.setdefault("posts", {})

    token = os.getenv("TIKTOK_ACCESS_TOKEN", "").strip()
    if not token:
        if needs_token(queue, state):
            print(
                "Há trabalho pendente, mas o secret TIKTOK_ACCESS_TOKEN ainda não foi configurado.",
                file=sys.stderr,
            )
            return 2
        print("Nenhum post pendente. Runner online está pronto e aguardando fila.")
        return 0

    changed = poll_existing(token, state)

    now = utc_now()
    candidates = []
    for post in queue.get("posts", []):
        post_id = str(post.get("id", "")).strip()
        if not post_id or post_id in state["posts"]:
            continue
        if post.get("approved") is not True or not post.get("consented_at"):
            continue
        scheduled = parse_time(post.get("scheduled_at"))
        if scheduled and scheduled <= now:
            candidates.append((scheduled, post))

    candidates.sort(key=lambda item: item[0])

    if candidates:
        creator_info = get_creator_info(token)
        print(
            "[creator]",
            creator_info.get("creator_username")
            or creator_info.get("creator_nickname")
            or "conta autorizada",
        )

        for _, post in candidates[:MAX_NEW_POSTS_PER_RUN]:
            post_id = str(post["id"])
            publish_id = submit_post(token, post, creator_info)
            state["posts"][post_id] = {
                "publish_id": publish_id,
                "status": "PROCESSING_DOWNLOAD",
                "submitted_at": iso_now(),
                "last_checked_at": iso_now(),
                "video_url": post["video_url"],
                "title": post.get("title", ""),
                "privacy_level": post["privacy_level"],
            }
            changed = True
            print(f"[submitted] {post_id}: {publish_id}")

    if changed:
        save_json(STATE_PATH, state)
        print("Estado atualizado.")
    else:
        print("Nenhuma alteração nesta execução.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
