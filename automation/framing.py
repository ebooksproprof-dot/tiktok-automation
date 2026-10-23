"""Product-safe framing: whole image in a text-free box, blurred background."""


def product_geometry(width, height):
    if any(type(x) is not int or not 2 <= x <= 16384 for x in (width, height)):
        raise ValueError('Invalid source dimensions')
    factor = min(1080 / width, 720 / height)
    w, h = max(2, int(width * factor) // 2 * 2), max(2, int(height * factor) // 2 * 2)
    return dict(width=w, height=h, x=(1080-w)//2, y=500+(720-h)//2)


def product_frame_filter(width, height):
    box = product_geometry(width, height)
    return ('[0:v]split=2[background][foreground];'
        '[background]scale=270:480:force_original_aspect_ratio=increase,'
        'crop=270:480,gblur=sigma=18,eq=brightness=-0.16,scale=1080:1920[blur];'
        f"[foreground]scale={box['width']}:{box['height']},setsar=1[full];"
        f"[blur][full]overlay={box['x']}:{box['y']},setsar=1,fps=30")
