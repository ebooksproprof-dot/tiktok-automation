#!/usr/bin/env python3
"""Optional Buffer Free route; uses the existing queue, state and cloud workflow.

Official schema: https://developers.buffer.com/reference.html (2026-10-15).
Workflows default to Buffer; credentials and strict channel validation are required.
"""
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import tiktok_runner as common
import buffer_quota
from media_quality import validate
from visual_library import require_evidence

POST_FIELDS = "id channelId status schedulingType dueAt sentAt externalLink"
CHANNEL_QUERY = """query($input: ChannelInput!) {
  channel(input: $input) { id name service organizationId externalLink
    isDisconnected isLocked isQueuePaused
    metadata { ... on TiktokMetadata { defaultToReminders } }
  }
}"""
CREATE_QUERY = """mutation($input: CreatePostInput!) {
  createPost(input: $input) { __typename
    ... on PostActionSuccess { post { """ + POST_FIELDS + """ } }
  }
}"""


class Client:
    def __init__(self, state):
        self.token = os.getenv("BUFFER_API_KEY", "").strip()
        if not self.token:
            raise RuntimeError("BUFFER_API_KEY missing; add it as a GitHub Actions secret")
        self.state = state
        self.calls = 0

    def check_budget(self, required=1):
        buffer_quota.check(self.state, common.utc_now(), required, self.calls)

    def call(self, query, variables):
        self.check_budget()
        self.calls += 1
        buffer_quota.record_attempt(self.state, common.utc_now())
        common.save_json(common.STATE_PATH, self.state)
        request = urllib.request.Request("https://api.buffer.com", method="POST",
            data=json.dumps({"query": query, "variables": variables}).encode(),
            headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json"})
        # Never retry a mutation here: a timeout can mean the post was created.
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                buffer_quota.record_headers(self.state, response.headers, common.utc_now())
                common.save_json(common.STATE_PATH, self.state)
                result = json.load(response)
        except urllib.error.HTTPError as exc:
            buffer_quota.record_error(self.state, exc.code, exc.headers, common.utc_now())
            common.save_json(common.STATE_PATH, self.state)
            raise RuntimeError(f"Buffer HTTP {exc.code}; body omitted; no automatic resubmission") from None
        except (urllib.error.URLError, TimeoutError, ValueError):
            buffer_quota.record_error(self.state, 503, {}, common.utc_now())
            common.save_json(common.STATE_PATH, self.state)
            raise RuntimeError("Buffer response unavailable; reconcile before any resubmission") from None
        if not isinstance(result, dict) or result.get("errors") or not isinstance(result.get("data"), dict):
            buffer_quota.record_error(self.state, 503, {}, common.utc_now())
            common.save_json(common.STATE_PATH, self.state)
            raise RuntimeError("Buffer GraphQL request failed; response body omitted")
        buffer_quota.record_success(self.state)
        common.save_json(common.STATE_PATH, self.state)
        return result["data"]


def check_channel(channel, channel_id):
    if (channel.get("id") != channel_id or channel.get("service") != "tiktok"
            or channel.get("name", "").removeprefix("@") != common.EXPECTED_USERNAME):
        raise ValueError("Buffer channel identity mismatch")
    if any(channel.get(k) is not False for k in ("isDisconnected", "isLocked", "isQueuePaused")):
        raise ValueError("Buffer channel disconnected, locked or paused")
    if (channel.get("metadata") or {}).get("defaultToReminders") is not False:
        raise ValueError("Configure automatic TikTok publishing in Buffer first")


def prepare(post, state, channel_id):
    quality = post.get("quality") or {}
    if post.get("publication_provider") != "buffer":
        raise ValueError("Post not assigned to Buffer")
    if quality.get("technical_pass") is not True or quality.get("editorial_approved") is not True:
        raise ValueError("Technical and editorial review required")
    from visual_library import history
    require_evidence(post, history({}, state))
    sha = quality.get("sha256", "")
    if not re.fullmatch(r"[0-9a-f]{64}", sha):
        raise ValueError("Missing media fingerprint")
    if post.get("id") in state["posts"] or any(p.get("sha256") == sha for p in state["posts"].values()):
        raise ValueError("Media already submitted through a provider")
    if post.get("public_url") or post.get("metricool_post_id"):
        raise ValueError("Post already submitted through Metricool")
    when = common.parse_time(post.get("scheduled_at"))
    now = common.utc_now()
    if not when or not now + timedelta(minutes=5) <= when <= now + timedelta(hours=26):
        raise ValueError("Schedule must be 5 minutes to 26 hours in the future")
    day = when.astimezone(ZoneInfo('America/Fortaleza')).date()
    reserved = set()
    for key, previous in state['posts'].items():
        prior = previous.get('scheduled_at')
        if isinstance(prior, dict):
            raw = prior.get('dateTime')
            prior = common.parse_time(raw) if raw else None
            if prior and raw and not re.search(r'(Z|[+-]\d\d:\d\d)$', raw):
                prior = prior.replace(tzinfo=ZoneInfo(previous['scheduled_at'].get('timezone', 'America/Fortaleza')))
        else:
            prior = common.parse_time(prior)
        if prior and prior.astimezone(ZoneInfo('America/Fortaleza')).date() == day:
            reserved.add(key)
            if prior == when:
                raise ValueError('Publication slot already reserved')
    if len(reserved) >= 2:
        raise ValueError('Daily maximum of two publication reservations reached')
    text = post.get("title", "").strip()
    if not text or len(text) > 2200 or len(re.findall(r"(?<!\w)#\w+", text)) > 5:
        raise ValueError("Caption exceeds TikTok limits or is empty")
    url = post.get("video_url", "")
    prefixes = ("https://ebooksproprof-dot.github.io/tiktok-automation/public/rendered/daily/",
                "https://raw.githubusercontent.com/ebooksproprof-dot/tiktok-automation/",
                "https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/media-")
    if not url.startswith(prefixes) or not url.endswith(".mp4"):
        raise ValueError("Media must use the existing HTTPS repository hosting")
    return {"channelId": channel_id, "text": text, "schedulingType": "automatic",
            "mode": "customScheduled", "dueAt": when.isoformat(), "needsApproval": False,
            "saveToDraft": False, "aiAssisted": True,
            "metadata": {"tiktok": {"isAiGenerated": True}},
            "assets": [{"video": {"url": url}}]}


def verify_hosted(post):
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / "video.mp4"
        with urllib.request.urlopen(post["video_url"], timeout=45) as response, target.open("wb") as out:
            total = 0
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > 20_000_000:
                    raise ValueError("Hosted media exceeds budget")
                out.write(chunk)
        if validate(target)["sha256"] != post["quality"]["sha256"]:
            raise ValueError("Hosted media differs from reviewed video")


def record_remote(entry, remote, channel_id):
    if remote.get("channelId") != channel_id or remote.get("id") != entry.get("buffer_post_id"):
        raise ValueError("Buffer post identity mismatch")
    entry.update(last_checked_at=common.iso_now(), buffer_status=remote.get("status"), publicly_verified=False)
    if remote.get("schedulingType") != "automatic":
        entry["status"] = "BLOCKED_NOTIFICATION"
        return
    status = remote.get("status")
    url = remote.get("externalLink") or ""
    # Retain only public TikTok permalink shapes, never arbitrary URLs or query tokens.
    public_link = re.match(r"https://(?:www\.)?tiktok\.com/@[A-Za-z0-9_.]+/video/\d+(?=$|[?#])", url)
    entry['buffer_external_link'] = public_link.group(0) if public_link else None
    entry['buffer_sent_at_present'] = bool(remote.get('sentAt'))
    pattern = r"https://(?:www\.)?tiktok\.com/@" + re.escape(common.EXPECTED_USERNAME) + r"/video/(\d+)(?:\?.*)?"
    match = re.fullmatch(pattern, url)
    if status == "sent" and remote.get("sentAt") and match:
        canonical_url = 'https://www.tiktok.com/@' + common.EXPECTED_USERNAME + '/video/' + match[1]
        entry.pop('evidence_pending_reason', None)
        entry.update(status="PUBLISH_COMPLETE", publicly_verified=True, public_urls=[canonical_url],
                     publicly_available_post_id=[match[1]],
                     verification_source="Buffer API sent + automatic + exact-account externalLink")
    elif status == "error":
        entry["status"] = "FAILED"
    elif status in ("scheduled", "sending"):
        entry["status"] = status.upper()
        scheduled = common.parse_time(entry.get("scheduled_at"))
        if scheduled is None:
            entry["status"] = "BLOCKED_SCHEDULE_MISSING"
        elif status == "scheduled" and common.parse_time(remote.get("dueAt")) != scheduled:
            entry["status"] = "BLOCKED_SCHEDULE_MISMATCH"
        elif scheduled < common.utc_now() - timedelta(hours=2):
            # Continue read-only reconciliation; never resubmit an overdue remote post.
            entry["status"] = "PUBLICATION_OVERDUE"
    else:
        entry["status"] = "AWAITING_PUBLIC_EVIDENCE"
        entry['evidence_pending_reason'] = ('PUBLIC_LINK_MISSING' if not url else
            'PUBLIC_LINK_FORMAT_OR_ACCOUNT_MISMATCH' if not match else
            'SENT_TIMESTAMP_MISSING' if not remote.get('sentAt') else 'STATUS_NOT_SENT')


def submit(client, post, state, channel_id):
    payload = prepare(post, state, channel_id)
    verify_hosted(post)
    client.check_budget(required=2)  # Reserve create + read-back before durable intent.
    entry = dict(provider="buffer", status="SUBMISSION_UNKNOWN", submitted_at=common.iso_now(),
                 sha256=post["quality"]["sha256"], video_url=post["video_url"],
                 concept=post.get("concept"), script_sha256=post.get("script_sha256"),
                 script_lines=post.get('script_lines', []),
                 source_urls=post['quality'].get('source_urls', []),
                 visual_sources=post['quality'].get('visual_sources', []),
                 scheduled_at=post["scheduled_at"], publicly_verified=False,
                 recovery="Reconcile Buffer planner by timestamp, media and caption before retrying")
    state["posts"][post["id"]] = entry
    common.checkpoint(state)  # A failed durable checkpoint prevents the external write.
    result = client.call(CREATE_QUERY, {"input": payload})["createPost"]
    remote = result.get("post") or {}
    if result.get("__typename") != "PostActionSuccess" or not remote.get("id"):
        raise RuntimeError("Buffer did not return a post ID; reconcile; do not blindly retry")
    entry["buffer_post_id"] = remote["id"]
    common.checkpoint(state)
    # Read-back, not just the create response, confirms acceptance.
    fetched = client.call("query($input: PostInput!) { post(input: $input) { " + POST_FIELDS + " } }",
                          {"input": {"id": remote["id"]}})["post"]
    record_remote(entry, fetched, channel_id)
    common.checkpoint(state)



def pending_reconciliation(state):
    """Reuse confirmed scheduling until due; throttle unresolved readbacks across runs."""
    now = common.utc_now()
    pending = []
    for entry in state['posts'].values():
        if (entry.get('provider') != 'buffer' or not entry.get('buffer_post_id')
                or entry.get('publicly_verified') or entry.get('status') == 'FAILED'):
            continue
        due = common.parse_time(entry.get('scheduled_at'))
        checked = common.parse_time(entry.get('last_reconcile_attempt_at') or entry.get('last_checked_at'))
        if entry.get('status') == 'SCHEDULED' and due and now < due:
            continue
        if checked and now < checked + timedelta(minutes=30):
            continue
        pending.append(entry)
    return pending


def main(check_only=False):
    state = common.load_json(common.STATE_PATH, {"posts": {}})
    state.setdefault("posts", {})
    submitted = blocked = 0
    try:
        channel_id = os.getenv("BUFFER_CHANNEL_ID", "").strip()
        if not channel_id:
            client = Client(state)
            # Bootstrap without requesting or printing account emails or secrets.
            result = client.call("query { account { organizations { id } } }", {})
            orgs = result["account"]["organizations"]
            if len(orgs) != 1:
                raise RuntimeError("Configure BUFFER_CHANNEL_ID; account has multiple or no organizations")
            result = client.call("query($input: ChannelsInput!) { channels(input: $input) { id name service } }",
                                 {"input": {"organizationId": orgs[0]["id"]}})
            matches = [c for c in result["channels"] if c.get("service") == "tiktok"
                       and c.get("name", "").removeprefix("@") == common.EXPECTED_USERNAME]
            if len(matches) != 1:
                raise RuntimeError("Connect exactly the expected TikTok account to Buffer first")
            print("Set GitHub variable BUFFER_CHANNEL_ID=" + matches[0]["id"])
            return 2  # Discovery never enables publishing.
        queue = common.load_json(common.QUEUE_PATH, {"posts": []}) if not check_only else {"posts": []}
        pending = pending_reconciliation(state)
        eligible = 0
        for post in queue['posts']:
            try:
                prepare(post, state, channel_id)
                eligible += 1
            except (ValueError, KeyError):
                continue
        if not check_only and not pending and not eligible:
            print("Buffer: no due reconciliation or eligible submission; 0 API calls")
            blocked = sum(p.get('provider') == 'buffer' and p.get('status') == 'SUBMISSION_UNKNOWN'
                          and not p.get('buffer_post_id') for p in state['posts'].values())
            return 2 if blocked else 0
        client = Client(state)
        required = 5 if check_only else bool(pending) + (2 + 2 * min(eligible, 2) if eligible else 0)
        # Publishing reserves the full cycle; read-only reconciliation needs no channel query.
        client.check_budget(required=required)
        if check_only or eligible:
            channel = client.call(CHANNEL_QUERY, {"input": {"id": channel_id}})["channel"]
            check_channel(channel, channel_id)
            print("Buffer channel verified: @" + common.EXPECTED_USERNAME)
        if check_only:
            print("Read-only check complete; no publication attempted")
            return 0
        if len(pending) > 10:
            raise RuntimeError("Too many unresolved Buffer posts; reconcile before continuing")
        if pending:
            for entry in pending:
                entry['last_reconcile_attempt_at'] = common.iso_now()
            common.save_json(common.STATE_PATH, state)
            selections = [f'p{i}: post(input: {{id: {json.dumps(p["buffer_post_id"])}}}) {{ {POST_FIELDS} }}'
                          for i, p in enumerate(pending)]
            response = client.call("query { " + " ".join(selections) + " }", {})
            for i, entry in enumerate(pending):
                record_remote(entry, response[f"p{i}"], channel_id)
        candidates = []
        for post in queue["posts"]:
            if post.get("publication_provider") != "buffer":
                continue
            if post.get("id") in state["posts"] or not post.get("id", "").startswith("casasem-"):
                continue
            when = common.parse_time(post.get("scheduled_at"))
            if when and when <= common.utc_now() + timedelta(hours=26):
                try:
                    prepare(post, state, channel_id)
                    candidates.append(post)
                except ValueError as exc:
                    blocked += 1
                    print(f"::warning::{post['id']}: {exc}")
        if candidates:
            result = client.call("""query($input: PostsInput!) { posts(input: $input) {
                edges { node { channelId } } pageInfo { hasNextPage }
            } }""", {"input": {"organizationId": channel["organizationId"],
                                 "filter": {"status": ["scheduled", "sending"]}}})["posts"]
            if result["pageInfo"]["hasNextPage"]:
                raise RuntimeError("Buffer queue truncated; cannot verify free queue capacity")
            occupied = sum(e["node"]["channelId"] == channel_id for e in result.get("edges") or [])
            for post in sorted(candidates, key=lambda p: p["scheduled_at"])[:min(2, max(0, 10 - occupied))]:
                submit(client, post, state, channel_id)
                submitted += 1
            blocked += max(0, min(2, len(candidates)) - submitted)
        blocked += sum(p.get("provider") == "buffer" and not p.get("publicly_verified")
                       and p.get("status") not in ("SCHEDULED", "SENDING") for p in state["posts"].values())
        return 2 if blocked else 0
    finally:
        common.save_json(common.STATE_PATH, state)
        common.summary(state, blocked, submitted)


if __name__ == "__main__":
    try:
        raise SystemExit(main(check_only="--check" in sys.argv))
    except Exception as exc:
        print(f"::error::{type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
