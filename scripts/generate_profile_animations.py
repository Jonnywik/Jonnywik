from math import cos, pi, sin
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
INK = (8, 14, 20)
GRID = (32, 48, 58)
TEAL = (45, 212, 191)
MINT = (169, 249, 236)
AMBER = (251, 188, 93)
WHITE = (220, 248, 243)


def cubic(start, control_one, control_two, end, steps: int = 34):
    points = []
    for step in range(steps + 1):
        value = step / steps
        inverse = 1 - value
        x = (
            inverse**3 * start[0]
            + 3 * inverse**2 * value * control_one[0]
            + 3 * inverse * value**2 * control_two[0]
            + value**3 * end[0]
        )
        y = (
            inverse**3 * start[1]
            + 3 * inverse**2 * value * control_one[1]
            + 3 * inverse * value**2 * control_two[1]
            + value**3 * end[1]
        )
        points.append((x, y))
    return points


def chained_cubics(segments, vertical_offset: float = 0):
    points = []
    for index, segment in enumerate(segments):
        curve = cubic(*segment)
        if index:
            curve = curve[1:]
        points.extend((x, y + vertical_offset) for x, y in curve)
    return points


def signal_transit_routes(t: float):
    """Return three quietly drifting transit routes that converge on the signal cluster."""
    route_segments = [
        [
            ((-40, 373), (105, 260), (237, 444), (410, 316)),
            ((410, 316), (542, 205), (612, 232), (735, 263)),
            ((735, 263), (862, 294), (933, 166), (1037, 131)),
            ((1037, 131), (1110, 112), (1160, 71), (1235, 49)),
        ],
        [
            ((-40, 414), (126, 309), (250, 462), (432, 343)),
            ((432, 343), (572, 252), (647, 297), (765, 284)),
            ((765, 284), (891, 272), (951, 189), (1056, 145)),
            ((1056, 145), (1123, 118), (1184, 89), (1238, 63)),
        ],
        [
            ((-40, 322), (115, 230), (242, 390), (392, 286)),
            ((392, 286), (523, 190), (614, 191), (726, 233)),
            ((726, 233), (840, 274), (929, 201), (1018, 114)),
            ((1018, 114), (1094, 58), (1154, 69), (1230, 22)),
        ],
    ]
    paths = []
    for index, segments in enumerate(route_segments):
        drift = sin(t * 0.78 + index * 0.82) * (2.1 + index * 0.55)
        paths.append(chained_cubics(segments, drift))
    return paths


def point_on_route(points, progress: float):
    location = max(0, min(len(points) - 1, int(progress % 1 * (len(points) - 1))))
    return points[location]


def draw_packet(canvas: Image.Image, points, progress: float, color=TEAL, size: int = 3):
    """Draw one directional signal packet with a short fading wake."""
    wake = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    wake_draw = ImageDraw.Draw(wake)
    for offset in range(7, -1, -1):
        x, y = point_on_route(points, progress - offset * 0.018)
        radius = max(1, size - offset // 3)
        alpha = 24 + (7 - offset) * 25
        wake_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, alpha))
    canvas.alpha_composite(wake.filter(ImageFilter.GaussianBlur(3)))
    crisp = ImageDraw.Draw(canvas, "RGBA")
    x, y = point_on_route(points, progress)
    crisp.ellipse((x - size, y - size, x + size, y + size), fill=(*color, 245), outline=(*WHITE, 205), width=1)


def glow(canvas: Image.Image, x: int, y: int, color, radius: int):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, 155))
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius * 1.25)))
    crisp = ImageDraw.Draw(canvas)
    crisp.ellipse((x - radius // 2, y - radius // 2, x + radius // 2, y + radius // 2), fill=(*color, 255), outline=(*WHITE, 240), width=1)


def draw_grid(draw: ImageDraw.ImageDraw, width: int, height: int):
    for x in range(0, width + 1, 60):
        draw.line((x, 0, x, height), fill=(*GRID, 54), width=1)
    for y in range(0, height + 1, 60):
        draw.line((0, y, width, y), fill=(*GRID, 54), width=1)


def hero_frame(frame: int, width: int = 1200, height: int = 420) -> Image.Image:
    t = frame / 32 * pi * 2
    image = Image.new("RGBA", (width, height), (*INK, 255))
    glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_draw.ellipse((340, 152, 913, 510), fill=(*TEAL, 22))
    glow_draw.ellipse((754, 45, 1165, 274), fill=(*TEAL, 10))
    image.alpha_composite(glow_layer.filter(ImageFilter.GaussianBlur(104)))
    draw = ImageDraw.Draw(image, "RGBA")
    draw_grid(draw, width, height)
    draw.rectangle((1, 1, width - 2, height - 2), outline=(*WHITE, 25), width=1)

    scan_x = 518 + sin(t * 0.68) * 174
    scan_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    scan_draw = ImageDraw.Draw(scan_layer)
    scan_draw.rectangle((scan_x - 22, 56, scan_x + 22, height - 42), fill=(*TEAL, 8))
    image.alpha_composite(scan_layer.filter(ImageFilter.GaussianBlur(22)))

    routes = signal_transit_routes(t)
    for route_index, points in enumerate(routes):
        opacity = 72 + route_index * 18
        draw.line(points, fill=(*TEAL, opacity), width=1, joint="curve")
    draw.line(routes[0], fill=(*MINT, 112), width=2, joint="curve")

    for route, progress, size in [
        (routes[0], frame / 32 * 0.55 + 0.05, 3),
        (routes[0], frame / 32 * 0.38 + 0.60, 2),
        (routes[1], frame / 32 * 0.48 + 0.22, 3),
        (routes[2], frame / 32 * 0.43 + 0.46, 2),
    ]:
        draw_packet(image, route, progress, TEAL, size)

    for x, y, color, radius, phase in [
        (735, 261, TEAL, 10, 0.0),
        (1039, 132, AMBER, 8, 0.7),
        (1106, 97, MINT, 7, 1.3),
    ]:
        drift = sin(t * 0.76 + phase) * 2
        pulse = int((sin(t * 1.15 + phase) + 1) * 1.4)
        glow(image, x, int(y + drift), color, radius + pulse)

    marker_draw = ImageDraw.Draw(image, "RGBA")
    for x, y, alpha in [(1000, 88, 128), (1080, 67, 86), (1144, 55, 70)]:
        marker_draw.ellipse((x - 1, y - 1, x + 1, y + 1), fill=(*MINT, alpha))

    return image.convert("RGB").quantize(colors=108, method=Image.Quantize.MEDIANCUT)


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

    for progress, size in [
        (frame / 24 * 0.56 + 0.06, 3),
        (frame / 24 * 0.42 + 0.53, 2),
    ]:
        draw_packet(image, primary, progress, TEAL, size)

    for x, phase in [(150, 0), (600, 0.75), (1050, 1.5)]:
        y = 69 + sin(t * 0.8 + phase) * 2.2
        glow(image, x, int(y), TEAL, 5 + int((sin(t * 1.25 + phase) + 1) * 1.15))
    return image.convert("RGB").quantize(colors=72, method=Image.Quantize.MEDIANCUT)


def save_gif(path: Path, frames, duration: int):
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=duration, loop=0, disposal=2, optimize=True)


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    save_gif(ASSETS / "profile-signal-field.gif", [hero_frame(frame) for frame in range(32)], 84)
    save_gif(ASSETS / "route-pulse-strip.gif", [strip_frame(frame) for frame in range(24)], 90)
    print(ASSETS / "profile-signal-field.gif")
    print(ASSETS / "route-pulse-strip.gif")


if __name__ == "__main__":
    main()
