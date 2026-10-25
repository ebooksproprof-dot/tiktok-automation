"""Measured CPU captions. No change to narration timing or editorial state."""
import math
from pathlib import Path

REVISION = 'measured-v51'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
MAX_WIDTH = 864


def layout(text):
    from PIL import ImageFont
    words = text.split()
    if not words or any(ord(c) < 32 and c not in '\n\t\r' for c in text):
        raise ValueError('Empty or unsupported caption')
    for size in (58, 54, 50, 46, 42):
        font = ImageFont.truetype(FONT, size)
        lines = []
        for word in words:
            if font.getlength(word) > MAX_WIDTH:
                break
            if lines and font.getlength(lines[-1] + ' ' + word) <= MAX_WIDTH:
                lines[-1] += ' ' + word
            else:
                lines.append(word)
        else:
            if len(lines) <= 2:
                return '\n'.join(lines), size
    raise ValueError('Caption cannot fit safely; shorten editorial text')


def filters(folder, timings):
    folder = Path(folder)
    # Paths are generated internally; reject filter metacharacters rather than guessing escapes.
    if any(c in str(folder) for c in "':,;[]\\"):
        raise ValueError('Unsafe caption directory')
    result, previous = [], 0.0
    for index, (start, end, text) in enumerate(timings):
        if not all(math.isfinite(t) for t in (start, end)) or start < previous - 1e-6 or end <= start:
            raise ValueError('Invalid or overlapping caption timings')
        rendered, size = layout(text)
        path = folder / f'caption-v51-{index}.txt'
        path.write_text(rendered, encoding='utf8')
        result.append(
            f"drawtext=fontfile={FONT}:textfile={path}:expansion=none:fontsize={size}:"
            "fontcolor=white:box=1:boxcolor=black@0.78:boxborderw=18:"
            "x=(w-text_w)/2:y=1320:"
            f"alpha='min(1,max(0,(t-{start:.6f})/0.08))':"
            f"enable='gte(t,{start:.6f})*lt(t,{end:.6f})'")
        previous = end
    return result
