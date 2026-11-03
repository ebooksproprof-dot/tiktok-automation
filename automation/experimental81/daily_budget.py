"""Conservative ZeroGPU request planner; NOT a provider quota balance.

Every call is a non-retryable claim. Its durable CAS persistence must be supplied by
the caller BEFORE a remote generation is submitted. Do not auto-post outputs.
"""
from datetime import datetime, timedelta, timezone
import copy
import math

WINDOW_SECONDS = 24 * 60 * 60
DOCUMENTED_SECONDS = {'anonymous': 120, 'free': 300}
# Estimation only: Wan 2.2 5s, 480x832, four steps ~= 50.5 s by Space
# source formula; 55 reserves extra margin but is NOT observed billing.
ESTIMATED_PER_CLIP_SECONDS = 55.0
MAX_CLAIMS = 512


class QuotaError(ValueError):
    pass


def timestamp(value):
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise QuotaError('UTC_AWARE_NOW_REQUIRED')
    return value.astimezone(timezone.utc)


def fresh():
    return {'schema_version': 1, 'window_start': None, 'tier': None,
            'claims': [], 'window_claim_ids': []}


def reserve(state, request_id, now, tier='anonymous', estimated_seconds=ESTIMATED_PER_CLIP_SECONDS):
    """Pure function; save result with remote CAS before sending the API request.

    An authenticated 'free' entitlement must be independently verified. Passing
    tier='free' does NOT log in, obtain credits, or authorize paid billing.
    """
    now = timestamp(now)
    if tier not in DOCUMENTED_SECONDS:
        raise QuotaError('UNKNOWN_OR_PAID_TIER_FORBIDDEN')
    if not isinstance(request_id, str) or len(request_id) != 64 or any(c not in '0123456789abcdef' for c in request_id):
        raise QuotaError('REQUEST_SHA256_REQUIRED')
    if not isinstance(estimated_seconds, (int, float)) or not math.isfinite(estimated_seconds) or not 20 <= estimated_seconds <= 120:
        raise QuotaError('INVALID_ESTIMATED_GPU_SECONDS')
    if not isinstance(state, dict) or state.get('schema_version') != 1:
        raise QuotaError('BAD_LEDGER_SCHEMA')
    value = copy.deepcopy(state)
    all_claims = value.get('claims', [])
    if not isinstance(all_claims, list) or len(all_claims) >= MAX_CLAIMS:
        raise QuotaError('CLAIM_LEDGER_FULL_REQUIRES_MANUAL_ARCHIVE')
    if any(c.get('request_sha256') == request_id for c in all_claims):
        raise QuotaError('DUPLICATE_OR_UNKNOWN_RESULT_NO_RETRY')
    start = value.get('window_start')
    if start is None:
        start_time = now
        value['window_start'] = now.isoformat()
        value['tier'] = tier
        value['window_claim_ids'] = []
    else:
        try:
            start_time = timestamp(datetime.fromisoformat(start))
        except (ValueError, TypeError):
            raise QuotaError('INVALID_WINDOW_START') from None
        if now < start_time:
            raise QuotaError('CLOCK_MOVED_BACKWARDS')
        if now >= start_time + timedelta(seconds=WINDOW_SECONDS):
            start_time = now
            value['window_start'] = now.isoformat()
            value['tier'] = tier
            value['window_claim_ids'] = []
        elif value.get('tier') != tier:
            raise QuotaError('TIER_CHANGE_WITHIN_WINDOW_NOT_ALLOWED')
    ids = value.get('window_claim_ids')
    if not isinstance(ids, list) or any(not isinstance(x, str) for x in ids):
        raise QuotaError('BAD_WINDOW_CLAIMS')
    by_id = {c['request_sha256']: c for c in all_claims}
    if any(x not in by_id for x in ids):
        raise QuotaError('MISSING_HISTORICAL_CLAIM')
    reserved = sum(float(by_id[x]['estimated_seconds']) for x in ids)
    # Leave 5% unallocated for uncertainty. Provider may still debit differently.
    cap = 0.95 * DOCUMENTED_SECONDS[tier]
    if reserved + estimated_seconds > cap + 1e-6:
        raise QuotaError('DAILY_QUOTA_ESTIMATE_EXCEEDED')
    event = {'request_sha256': request_id, 'claimed_at': now.isoformat(),
             'estimated_seconds': float(estimated_seconds), 'status': 'RESERVED_NO_AUTO_RETRY'}
    all_claims.append(event)
    ids.append(request_id)
    value['claims'] = all_claims
    return value


def estimate_full_video(clips=6, seconds_per_clip=ESTIMATED_PER_CLIP_SECONDS, tier='anonymous'):
    if clips < 1 or tier not in DOCUMENTED_SECONDS:
        raise QuotaError('INVALID_ESTIMATE')
    required = clips * seconds_per_clip
    cap = 0.95 * DOCUMENTED_SECONDS[tier]
    return {'clips_required': clips, 'estimated_gpu_seconds': required,
            'documented_daily_quota_seconds': DOCUMENTED_SECONDS[tier],
            'unallocated_margin_seconds': DOCUMENTED_SECONDS[tier]-cap,
            'fits_theoretical_cap': required <= cap,
            'guaranteed_production': False,
            'observed_actual_quota_debit': False}


if __name__ == '__main__':
    import json
    print(json.dumps({t: estimate_full_video(tier=t) for t in DOCUMENTED_SECONDS}, indent=2))
