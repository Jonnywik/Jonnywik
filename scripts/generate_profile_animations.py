from math import pi, sin
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
PORTRAIT = ASSETS / "mikael-lim-portrait.png"
INK = (8, 14, 20)
GRID = (32, 48, 58)
TEAL = (45, 212, 191)
MINT = (169, 249, 236)
AMBER = (251, 188, 93)
VIOLET = (167, 139, 250)
WHITE = (220, 248, 243)
SLATE = (145, 169, 178)


def font(filename: str, size: int):
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{filename}", size)


FONT_NAME = font("DejaVuSans-Bold.ttf", 30)
FONT_ROLE = font("DejaVuSans-Bold.ttf", 14)
FONT_META = font("DejaVuSansMono.ttf", 11)
FONT_CHIP = font("DejaVuSans-Bold.ttf", 10)


def cubic(start, control_one, control_two, end, steps: int = 38):
    points = []
    for step in range(steps + 1):
        value = step / steps
        inverse = 1 - value
        x = inverse**3 * start[0] + 3 * inverse**2 * value * control_one[0] + 3 * inverse * value**2 * control_two[0] + value**3 * end[0]
        y = inverse**3 * start[1] + 3 * inverse**2 * value * control_one[1] + 3 * inverse * value**2 * control_two[1] + value**3 * end[1]
        points.append((x, y))
    return points


def chained_cubics(segments, vertical_offset: float = 0):
    points = []
    for index, segment in enumerate(segments):
        curve = cubic(*segment)
        points.extend(curve if index == 0 else curve[1:])
    return [(x, y + vertical_offset) for x, y in points]


def hero_routes(t: float):
    route_segments = [
        [
            ((246, 374), (372, 412), (482, 344), (642, 342)),
            ((642, 342), (787, 338), (879, 250), (1030, 218)),
            ((1030, 218), (1080, 197), (1126, 174), (1215, 170)),
        ],
        [
            ((246, 346), (382, 322), (499, 383), (646, 316)),
            ((646, 316), (790, 252), (869, 255), (986, 188)),
            ((986, 188), (1061, 143), (1127, 126), (1216, 116)),
        ],
        [
            ((258, 394), (392, 404), (494, 363), (662, 361)),
            ((662, 361), (806, 356), (901, 301), (1032, 270)),
            ((1032, 270), (1101, 243), (1153, 217), (1220, 205)),
        ],
    ]
    return [
        chained_cubics(segments, sin(t * 0.72 + index * 0.85) * (2 + index * 0.45))
        for index, segments in enumerate(route_segments)
    ]


def point_on_route(points, progress: float):
    location = max(0, min(len(points) - 1, int(progress % 1 * (len(points) - 1))))
    return points[location]


def draw_packet(canvas: Image.Image, points, progress: float, color=TEAL, size: int = 3):
    wake = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    wake_draw = ImageDraw.Draw(wake)
    for offset in range(8, -1, -1):
        x, y = point_on_route(points, progress - offset * 0.018)
        radius = max(1, size - offset // 3)
        wake_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, 24 + (8 - offset) * 24))
    canvas.alpha_composite(wake.filter(ImageFilter.GaussianBlur(3)))
    crisp = ImageDraw.Draw(canvas, "RGBA")
    x, y = point_on_route(points, progress)
    crisp.ellipse((x - size, y - size, x + size, y + size), fill=(*color, 245), outline=(*WHITE, 205), width=1)


def glow(canvas: Image.Image, x: int, y: int, color, radius: int, phase: float, frame: int):
    pulse = int((sin(frame / 32 * pi * 2 * 1.2 + phase) + 1) * 1.7)
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.ellipse((x - radius - pulse, y - radius - pulse, x + radius + pulse, y + radius + pulse), fill=(*color, 142))
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius * 1.3)))
    crisp = ImageDraw.Draw(canvas, "RGBA")
    ring = radius // 2 + pulse + 4
    crisp.ellipse((x - ring, y - ring, x + ring, y + ring), outline=(*color, 130), width=1)
    crisp.ellipse((x - radius // 2, y - radius // 2, x + radius // 2, y + radius // 2), fill=(*color, 255), outline=(*WHITE, 225), width=1)


def draw_grid(draw: ImageDraw.ImageDraw, width: int, height: int):
    for x in range(0, width + 1, 60):
        draw.line((x, 0, x, height), fill=(*GRID, 54), width=1)
    for y in range(0, height + 1, 60):
        draw.line((0, y, width, y), fill=(*GRID, 54), width=1)


def draw_chip(image: Image.Image, x: int, y: int, label: str, accent):
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    text_bounds = draw.textbbox((0, 0), label, font=FONT_CHIP)
    width = text_bounds[2] - text_bounds[0] + 26
    draw.rounded_rectangle((x, y, x + width, y + 26), radius=4, fill=(10, 22, 30, 214), outline=(*accent, 142), width=1)
    draw.ellipse((x + 10, y + 10, x + 15, y + 15), fill=(*accent, 238))
    draw.text((x + 21, y + 7), label, font=FONT_CHIP, fill=(*WHITE, 240))
    image.alpha_composite(layer)


def draw_profile_copy(image: Image.Image, frame: int):
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    scan_x = 354 + ((frame * 31) % 395)
    draw.rectangle((scan_x, 42, scan_x + 26, 280), fill=(*TEAL, 8))
    draw.text((332, 52), "MIKAEL C. LIM", font=FONT_NAME, fill=(*WHITE, 250))
    draw.text((334, 96), "IT STUDENT  /  SYSTEMS BUILDER", font=FONT_ROLE, fill=(*MINT, 238))
    draw.line((334, 126, 748, 126), fill=(*TEAL, 102), width=1)
    draw.text((334, 143), "BSIT · PLM · EXPECTED 2029", font=FONT_META, fill=(*SLATE, 250))
    draw.text((334, 168), "DEAN'S LISTER · 1.35 GPA", font=FONT_META, fill=(*AMBER, 245))
    draw.text((334, 196), "PROFILE SIGNALS / DESIGN · DATA · DELIVERY", font=FONT_META, fill=(*VIOLET, 230))
    image.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.15)))
    draw_chip(image, 334, 225, "UI/UX + DOCS", TEAL)
    draw_chip(image, 474, 225, "PYTHON + NEXT.JS", VIOLET)
    draw_chip(image, 647, 225, "SQL + DATA", AMBER)


def paste_portrait(image: Image.Image):
    portrait = Image.open(PORTRAIT).convert("RGBA")
    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle((35, 34, 299, 392), radius=14, fill=(*TEAL, 48))
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(16)))
    frame = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)
    draw.rounded_rectangle((40, 30, 294, 394), radius=12, fill=(8, 18, 25, 248), outline=(*TEAL, 180), width=1)
    draw.line((40, 52, 294, 52), fill=(*VIOLET, 105), width=1)
    draw.text((58, 37), "PROFILE / ACTIVE", font=FONT_META, fill=(*MINT, 220))
    image.alpha_composite(frame)
    portrait = portrait.resize((244, 344), Image.Resampling.LANCZOS)
    image.alpha_composite(portrait, (45, 47))
    frame_front = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame_front)
    draw.rounded_rectangle((40, 30, 294, 394), radius=12, outline=(*TEAL, 184), width=1)
    draw.rectangle((45, 362, 289, 391), fill=(7, 14, 20, 124))
    draw.text((58, 371), "M. LIM  /  PROFILE SIGNAL", font=FONT_META, fill=(*WHITE, 205))
    image.alpha_composite(frame_front)


def hero_frame(frame: int, width: int = 1200, height: int = 420) -> Image.Image:
    t = frame / 32 * pi * 2
    image = Image.new("RGBA", (width, height), (*INK, 255))
    haze = Image.new("RGBA", image.size, (0, 0, 0, 0))
    haze_draw = ImageDraw.Draw(haze)
    haze_draw.ellipse((270, 84, 868, 474), fill=(*TEAL, 18))
    haze_draw.ellipse((700, -42, 1188, 290), fill=(*VIOLET, 13))
    haze_draw.ellipse((875, 118, 1220, 430), fill=(*AMBER, 8))
    image.alpha_composite(haze.filter(ImageFilter.GaussianBlur(100)))
    draw = ImageDraw.Draw(image, "RGBA")
    draw_grid(draw, width, height)
    draw.rectangle((1, 1, width - 2, height - 2), outline=(*WHITE, 28), width=1)

    paste_portrait(image)
    draw_profile_copy(image, frame)

    routes = hero_routes(t)
    for points, color, opacity, stroke in [(routes[0], TEAL, 116, 2), (routes[1], MINT, 96, 1), (routes[2], VIOLET, 106, 1)]:
        route_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        ImageDraw.Draw(route_layer).line(points, fill=(*color, opacity), width=stroke, joint="curve")
        image.alpha_composite(route_layer)
    for route, progress, color, size in [
        (routes[0], frame / 32 * 0.62 + 0.04, TEAL, 3),
        (routes[0], frame / 32 * 0.40 + 0.51, AMBER, 2),
        (routes[1], frame / 32 * 0.49 + 0.18, MINT, 3),
        (routes[2], frame / 32 * 0.44 + 0.69, VIOLET, 2),
    ]:
        draw_packet(image, route, progress, color, size)

    for x, y, color, radius, phase, label in [
        (646, 331, TEAL, 10, 0.0, "ORIGIN"),
        (987, 188, AMBER, 8, 0.7, "EVIDENCE"),
        (1031, 218, MINT, 8, 1.3, "SYSTEM"),
        (1033, 270, VIOLET, 8, 1.8, "SOURCE"),
    ]:
        drift = sin(t * 0.74 + phase) * 2
        glow(image, x, int(y + drift), color, radius, phase, frame)
        label_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        ImageDraw.Draw(label_layer).text((x + 13, int(y + drift) - 5), label, font=FONT_META, fill=(*color, 235))
        image.alpha_composite(label_layer)

    marker = ImageDraw.Draw(image, "RGBA")
    for x, y, color in [(1112, 151, MINT), (1152, 129, AMBER), (1179, 108, VIOLET)]:
        marker.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(*color, 172))
    return image.convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT)


def strip_frame(frame: int, width: int = 1200, height: int = 138) -> Image.Image:
    t = frame / 24 * pi * 2
    image = Image.new("RGBA", (width, height), (*INK, 255))
    depth = Image.new("RGBA", image.size, (0, 0, 0, 0))
    depth_draw = ImageDraw.Draw(depth)
    depth_draw.ellipse((255, -70, 955, 194), fill=(*TEAL, 11))
    image.alpha_composite(depth.filter(ImageFilter.GaussianBlur(56)))
    draw = ImageDraw.Draw(image, "RGBA")
    primary = chained_cubics(
        [
            ((150, 69), (314, 17), (447, 118), (600, 69)),
            ((600, 69), (756, 20), (896, 16), (1050, 69)),
        ],
        sin(t * 0.8) * 2.2,
    )
    draw.line(primary, fill=(*TEAL, 116), width=2, joint="curve")
    draw.line(primary, fill=(*MINT, 56), width=1, joint="curve")
    for progress, size in [(frame / 24 * 0.56 + 0.06, 3), (frame / 24 * 0.42 + 0.53, 2)]:
        draw_packet(image, primary, progress, TEAL, size)
    for x, phase in [(150, 0), (600, 0.75), (1050, 1.5)]:
        y = 69 + sin(t * 0.8 + phase) * 2.2
        glow(image, x, int(y), TEAL, 5 + int((sin(t * 1.25 + phase) + 1) * 1.15), phase, frame)
    return image.convert("RGB").quantize(colors=72, method=Image.Quantize.MEDIANCUT)


def save_gif(path: Path, frames, duration: int):
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=duration, loop=0, disposal=2, optimize=True)


def main():
    if not PORTRAIT.exists():
        raise FileNotFoundError(f"Run scripts/prepare_profile_portrait.py first: {PORTRAIT}")
    ASSETS.mkdir(parents=True, exist_ok=True)
    save_gif(ASSETS / "profile-signal-field.gif", [hero_frame(frame) for frame in range(32)], 84)
    save_gif(ASSETS / "route-pulse-strip.gif", [strip_frame(frame) for frame in range(24)], 90)
    print(ASSETS / "profile-signal-field.gif")
    print(ASSETS / "route-pulse-strip.gif")


if __name__ == "__main__":
    main()
