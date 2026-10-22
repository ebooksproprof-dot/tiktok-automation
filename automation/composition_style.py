"""Original CasaSemEsforco graphics; bounded crops, never duplicated footage."""
import textwrap

BASE_CROP = 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30'


def shot_filter(width, height, index):
    # Only shift when the scaled source has 60px spare on each side.
    scaled_width = width * max(1080 / width, 1920 / height)
    if scaled_width < 1200 or width < 1080 or height < 1920:
        return BASE_CROP, 0
    shift = -60 if index % 2 == 0 else 60
    return ('scale=1080:1920:force_original_aspect_ratio=increase,'
            f'crop=1080:1920:x=(iw-ow)/2+{shift}:y=(ih-oh)/2,fps=30'), shift


def overlay(folder, hook, duration):
    lines = textwrap.wrap(hook, width=29, break_long_words=False)
    if not 1 <= len(lines) <= 2 or any(len(line)>29 for line in lines):
        return []  # Do not truncate meaning or draw overflowing headlines.
    title = folder/'hook-v4.txt'
    title.write_text('\n'.join(lines), encoding='utf8')
    font = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    return [
        'drawbox=x=54:y=265:w=972:h=140:color=black@0.70:t=fill:enable=lt(t\\,3)',
        f'drawtext=fontfile={font}:textfile={title}:fontsize=43:fontcolor=0x8EF0D0:x=(w-text_w)/2:y=290:enable=lt(t\\,3)',
        'drawbox=x=54:y=1480:w=972:h=8:color=white@0.28:t=fill',
        f'drawbox=x=54:y=1480:w=972:h=8:color=0x8EF0D0:t=fill:enable=gte(t\\,{duration*.75:.4f})',
    ]
