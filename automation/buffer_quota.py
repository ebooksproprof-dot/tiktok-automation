"""Persistent conservative Buffer quota accounting; no I/O, sleep or HTTP retries.

Caller must save state after record_attempt BEFORE HTTP, and after headers/error.
Count every attempted request, including uncertain writes. Never retry a mutation
just because its budget permits another attempt.
"""
import datetime as dt
from email.utils import parsedate_to_datetime
import re

WINDOWS = {900: 90, 86400: 90, 2592000: 900}
RUN_LIMIT = 8
UTC = dt.timezone.utc


class BudgetExceeded(RuntimeError):
    def __init__(self, reason, next_allowed_at=None):
        self.reason = reason
        self.next_allowed_at = next_allowed_at
        super().__init__('Buffer budget blocked: ' + reason +
                         ('; next_allowed_at=' + next_allowed_at if next_allowed_at else ''))


def instant(value):
    if isinstance(value, str):
        try:
            value = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError('INVALID_BUDGET_TIMESTAMP') from None
    if not isinstance(value, dt.datetime) or value.tzinfo is None:
        raise ValueError('INVALID_BUDGET_TIMESTAMP')
    return value.astimezone(UTC)


def stamp(value):
    return instant(value).isoformat().replace('+00:00', 'Z')


def bucket(state):
    result = state.setdefault('buffer_quota', {})
    if not isinstance(result, dict):
        raise ValueError('INVALID_BUDGET_STATE')
    result.setdefault('windows', {})
    if not isinstance(result['windows'], dict):
        raise ValueError('INVALID_BUDGET_STATE')
    return result


def usage(state, now):
    items = state.setdefault('buffer_api_usage', [])
    if not isinstance(items, list):
        raise ValueError('INVALID_BUDGET_STATE')
    parsed = [instant(value) for value in items]
    parsed = sorted(value for value in parsed if value > now - dt.timedelta(days=30))
    # Future timestamps are retained and counted conservatively after clock skew.
    items[:] = [stamp(value) for value in parsed]
    return parsed


def later(state, target):
    data = bucket(state)
    existing = data.get('next_allowed_at')
    if existing:
        target = max(target, instant(existing))
    data['next_allowed_at'] = stamp(target)
    return data['next_allowed_at']


def check(state, now, required=1, calls=0):
    """Reserve capacity conceptually; actual attempts are counted separately."""
    now = instant(now)
    if type(required) is not int or not 1 <= required <= RUN_LIMIT or type(calls) is not int or calls < 0:
        raise ValueError('INVALID_BUDGET_REQUEST')
    data = bucket(state)
    used = usage(state, now)
    if calls + required > RUN_LIMIT:
        raise BudgetExceeded('RUN_LIMIT')
    blocked_until = []
    if data.get('next_allowed_at') and instant(data['next_allowed_at']) > now:
        blocked_until.append(instant(data['next_allowed_at']))
    for seconds, limit in WINDOWS.items():
        recent = [value for value in used if value > now - dt.timedelta(seconds=seconds)]
        overflow = len(recent) + required - limit
        if overflow > 0:
            blocked_until.append(recent[overflow-1] + dt.timedelta(seconds=seconds))
    for policy in data['windows'].values():
        reset = instant(policy['reset_at']) if policy.get('reset_at') else None
        remaining = policy.get('remaining')
        if reset and reset > now and remaining is not None and remaining < required:
            blocked_until.append(reset)
    if blocked_until:
        raise BudgetExceeded('ROLLING_QUOTA_OR_BACKOFF', later(state, max(blocked_until)))
    return True


def record_attempt(state, now):
    """Call exactly once BEFORE HTTP, even if the response later has no headers."""
    now = instant(now)
    usage(state, now)
    state['buffer_api_usage'].append(stamp(now))
    for policy in bucket(state)['windows'].values():
        if policy.get('reset_at') and instant(policy['reset_at']) > now and policy.get('remaining') is not None:
            policy['remaining'] = max(0, policy['remaining'] - 1)
    return state


def header_values(headers, key):
    if headers is None:
        return []
    values = None
    if hasattr(headers, 'get_all'):
        values = headers.get_all(key)
    elif hasattr(headers, 'getlist'):
        values = headers.getlist(key)
    if values is None:
        values = []
        for name, value in headers.items():
            if str(name).lower() == key.lower():
                values.extend(value if isinstance(value, (list, tuple)) else [value])
    if isinstance(values, str):
        values = [values]
    return [str(value) for value in values if len(str(value)) <= 10000]


def structured(headers, key):
    parsed = {}
    for value in header_values(headers, key):
        for item in re.split(r',\s*(?=")', value):
            match = re.match(r'^\s*"([A-Za-z0-9_-]{1,64})"\s*;', item)
            if not match:
                continue
            attrs = {}
            for name, digits in re.findall(r';\s*([qrtw])\s*=\s*(\d+)\s*(?=;|$)', item):
                number = int(digits)
                if number <= 10**9:
                    attrs[name] = number
            parsed[match[1]] = attrs
    return parsed


def record_headers(state, headers, now):
    """Store only parsed quota/window/remaining/reset data, never raw headers/pk."""
    now = instant(now)
    data = bucket(state)
    limits = structured(headers, 'RateLimit-Policy')
    statuses = structured(headers, 'RateLimit')
    for name, policy in limits.items():
        seconds, quota = policy.get('w'), policy.get('q')
        if seconds not in WINDOWS or not isinstance(quota, int) or quota <= 0:
            continue
        unmapped = data['windows'].pop('unmapped:' + name, {})
        old = data['windows'].setdefault(str(seconds), unmapped)
        old.update(policy=name, window_seconds=seconds, quota=quota)
    known_names = {value.get('policy') for value in data['windows'].values()}
    for name, status in statuses.items():
        if name not in known_names and 'r' in status and 't' in status:
            data['windows'].setdefault('unmapped:' + name, {'policy': name})
    for old in data['windows'].values():
        status = statuses.get(old.get('policy'), {})
        if 'r' not in status or 't' not in status or status['t'] > 2592000:
            continue
        old.update(remaining=status['r'], reset_at=stamp(now + dt.timedelta(seconds=status['t'])),
                   observed_at=stamp(now))
    return state


def retry_at(headers, now):
    targets = []
    for value in header_values(headers, 'Retry-After'):
        try:
            if re.fullmatch(r'\s*\d+\s*', value):
                seconds = int(value)
                if seconds > 31536000:
                    # Preserve fail-closed behavior on implausibly large delays.
                    seconds = 31536000
                target = now + dt.timedelta(seconds=seconds)
            else:
                target = instant(parsedate_to_datetime(value))
            if target > now:
                targets.append(target)
        except (ValueError, TypeError, OverflowError):
            continue
    return max(targets) if targets else None


def record_error(state, code, headers, now):
    """Record a cooldown, not a retry. code=None denotes transport/parse failure."""
    now = instant(now)
    record_headers(state, headers, now)
    data = bucket(state)
    previous = data.get('consecutive_errors', 0)
    if type(previous) is not int or previous < 0:
        raise ValueError('INVALID_BUDGET_STATE')
    failures = min(previous + 1, 20)
    data['consecutive_errors'] = failures
    data['last_error_code'] = code if type(code) is int and 100 <= code <= 599 else 'TRANSPORT_OR_RESPONSE'
    # Small exponential backoff persists across runners; authentication gets 6h.
    delay = 21600 if code in (401, 403) else min(60 * 2**(failures-1), 3600)
    target = now + dt.timedelta(seconds=delay)
    if code in (429, 503):
        server_delay = retry_at(headers, now)
        if server_delay:
            target = max(target, server_delay)
        for policy in data['windows'].values():
            if policy.get('remaining') == 0 and policy.get('reset_at'):
                target = max(target, instant(policy['reset_at']))
    later(state, target)
    return state


def record_success(state):
    data = bucket(state)
    data['consecutive_errors'] = 0
    data.pop('last_error_code', None)
    # Never erase active Retry-After/quota constraints from another response.
    return state
