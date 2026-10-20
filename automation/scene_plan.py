"""Sequential source windows: never loop footage to fill narration."""
def plan(timings, duration, source_durations):
    if not timings or not source_durations:
        raise ValueError('SCENES_REQUIRED')
    offsets = [0.0] * len(source_durations)
    shots = []
    for i, (start, end, text) in enumerate(timings):
        length = (timings[i+1][0] if i+1 < len(timings) else duration) - start
        source = min(i * len(source_durations) // len(timings), len(source_durations)-1)
        if length <= 0 or offsets[source] + length > source_durations[source] - .05:
            raise ValueError('SOURCE_TOO_SHORT_WITHOUT_REPEATING: choose more adequate footage')
        shots.append((source, offsets[source], length))
        offsets[source] += length
    return shots
