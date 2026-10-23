"""Sequential source windows: never loop footage to fill narration."""
import math


def plan(timings, duration, source_durations):
    if not timings or not source_durations:
        raise ValueError('SCENES_REQUIRED')
    if (not math.isfinite(duration) or duration <= 0 or
        any(not math.isfinite(d) or d <= .05 for d in source_durations)):
        raise ValueError('INVALID_SCENE_DURATION')
    if abs(timings[0][0]) > 1e-8 or any(
        not math.isfinite(start) or not math.isfinite(end) or start < 0 or end <= start
        or end > duration + 1e-8 or (i+1 < len(timings) and end > timings[i+1][0] + 1e-8)
        for i, (start, end, _) in enumerate(timings)):
        raise ValueError('INVALID_SCENE_TIMING')
    capacities = [d - .05 for d in source_durations]
    if sum(capacities) + 1e-8 < duration:
        raise ValueError('SOURCE_TOO_SHORT_WITHOUT_REPEATING: choose more adequate footage')
    offsets = [0.0] * len(source_durations)
    shots = []
    for i, (start, end, text) in enumerate(timings):
        length = (timings[i+1][0] if i+1 < len(timings) else duration) - start
        source = min(i * len(source_durations) // len(timings), len(source_durations)-1)
        if length <= 0:
            raise ValueError('INVALID_SCENE_TIMING')
        shots.append((source, offsets[source], length))
        offsets[source] += length
    if all(used <= available for used, available in zip(offsets, capacities)):
        return shots
    # Unequal clip lengths: divide the narration by available footage instead of
    # assigning equal caption counts and incorrectly rejecting a sufficient pool.
    quotas = [duration * capacity / sum(capacities) for capacity in capacities]
    shots, offsets, source = [], [0.0] * len(capacities), 0
    for i, (start, end, text) in enumerate(timings):
        remaining = (timings[i+1][0] if i+1 < len(timings) else duration) - start
        while remaining > 1e-8:
            if quotas[source] - offsets[source] <= 1e-8:
                source += 1
            length = min(remaining, quotas[source] - offsets[source])
            shots.append((source, offsets[source], length))
            offsets[source] += length
            remaining -= length
    return shots


def require_minimum_capacity(durations, minimum=15.0):
    if not durations or any(not math.isfinite(d) or d <= .05 for d in durations):
        raise ValueError('INVALID_SCENE_DURATION')
    capacity = sum(d-.05 for d in durations)
    if capacity < minimum:
        raise ValueError(f'SOURCE_TOO_SHORT_WITHOUT_REPEATING: {capacity:.2f}s available; at least {minimum:.2f}s required before narration')
    return capacity
