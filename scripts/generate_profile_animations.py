from math import cos, pi, sin
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
TEAL = (45, 212, 191)
ORANGE = (251, 146, 60)
VIOLET = (167, 139, 250)
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


def original_routes(t: float):
    route_segments = [
        [
            ((-20, 355), (101, 241), (188, 445), (328, 321)),
            ((328, 321), (468, 197), (497, 190), (627, 283)),
            ((627, 283), (757, 376), (838, 322), (957, 194)),
            ((957, 194), (1076, 66), (1148, 126), (1220, 29)),
        ],
        [
            ((-40, 397), (82, 271), (213, 473), (355, 349)),
            ((355, 349), (497, 225), (520, 202), (644, 282)),
            ((644, 282), (768, 362), (873, 303), (990, 177)),
            ((990, 177), (1107, 51), (1177, 110), (1245, 25)),
        ],
        [
            ((-40, 314), (88, 214), (168, 405), (300, 286)),
            ((300, 286), (432, 167), (480, 154), (612, 249)),
            ((612, 249), (744, 344), (827, 296), (953, 173)),
            ((953, 173), (1079, 50), (1154, 112), (1230, 24)),
        ],
        [
            ((-40, 269), (86, 173), (199, 361), (323, 240)),
            ((323, 240), (447, 119), (500, 113), (625, 210)),
            ((625, 210), (750, 307), (842, 258), (963, 142)),
            ((963, 142), (1084, 26), (1153, 90), (1232, 14)),
        ],
    ]
    paths = []
    for index, segments in enumerate(route_segments):
        drift = sin(t * 0.8 + index * 0.72) * (3.4 + index * 0.6)
        paths.append(chained_cubics(segments, drift))
    accent = chained_cubics(
        [
            ((508, 446), (606, 357), (639, 321), (708, 302)),
            ((708, 302), (777, 283), (800, 187), (880, 156)),
            ((880, 156), (960, 125), (1020, 170), (1089, 72)),
        ],
        sin(t * 0.78 + 1.1) * 3.5,
    )
    return paths, accent


def draw_dashed_route(draw: ImageDraw.ImageDraw, points, color, shift: int, opacity: int, width: int = 2):
    for index in range(0, len(points) - 4, 5):
        if ((index // 5 + shift) % 7) in (0, 1, 2):
            draw.line(points[index:index + 5], fill=(*color, opacity), width=width, joint="curve")


def glow(canvas: Image.Image, x: int, y: int, color, radius: int):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, 155))
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius * 1.25)))
    crisp = ImageDraw.Draw(canvas)
    crisp.ellipse((x - radius // 2, y - radius // 2, x + radius // 2, y + radius // 2), fill=(*color, 255), outline=(*WHITE, 240), width=1)


def draw_grid(draw: ImageDraw.ImageDraw, width: int, height: int):
    for x in range(0, width + 1, 46):
        draw.line((x, 0, x, height), fill=(28, 42, 52, 105), width=1)
    for y in range(0, height + 1, 46):
        draw.line((0, y, width, y), fill=(28, 42, 52, 105), width=1)


def hero_frame(frame: int, width: int = 1200, height: int = 420) -> Image.Image:
    t = frame / 24 * pi * 2
    image = Image.new("RGBA", (width, height), (9, 13, 18, 255))
    glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_draw.ellipse((365, 140, 920, 520), fill=(*TEAL, 28))
    image.alpha_composite(glow_layer.filter(ImageFilter.GaussianBlur(95)))
    draw = ImageDraw.Draw(image, "RGBA")
    draw_grid(draw, width, height)
    draw.rectangle((1, 1, width - 2, height - 2), outline=(196, 221, 226, 34), width=1)

    routes, accent = original_routes(t)
    for line_index, points in enumerate(routes):
        draw_dashed_route(draw, points, TEAL, int(frame * 0.9 + line_index * 2), 106 + line_index * 20, 1)
    draw_dashed_route(draw, accent, TEAL, int(frame * 1.3), 166, 2)

    for x, y, color, radius, phase in [
        (723, 296, TEAL, 11, 0),
        (943, 150, ORANGE, 10, 0.7),
        (1070, 82, VIOLET, 9, 1.4),
    ]:
        drift = sin(t * 0.8 + phase) * 3
        glow(image, x, int(y + drift), color, radius + int((sin(t * 1.25 + phase) + 1) * 1.5))

    particle_draw = ImageDraw.Draw(image, "RGBA")
    for particle_index in range(15):
        route = routes[particle_index % len(routes)]
        location = int((particle_index * 37 + frame * (2 + particle_index % 3)) % (len(route) - 1))
        x, y = route[location]
        rise = sin(t * 1.45 + particle_index) * 3
        color = TEAL if particle_index % 6 else ORANGE if particle_index % 7 else VIOLET
        radius = 1 if particle_index % 3 else 2
        particle_draw.ellipse((x - radius, y + rise - radius, x + radius, y + rise + radius), fill=(*color, 185))

    return image.convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT)


def strip_frame(frame: int, width: int = 1200, height: int = 138) -> Image.Image:
    t = frame / 20 * pi * 2
    image = Image.new("RGBA", (width, height), (9, 13, 18, 255))
    draw = ImageDraw.Draw(image, "RGBA")
    primary = chained_cubics(
        [
            ((150, 69), (312, 14), (438, 124), (600, 69)),
            ((600, 69), (762, 14), (888, 14), (1050, 69)),
        ],
        sin(t * 0.9) * 3,
    )
    for index in range(4):
        offset = (index - 1.5) * 4
        points = [(x, y + offset + sin(t + index) * 1.7) for x, y in primary]
        draw_dashed_route(draw, points, TEAL, frame + index * 3, 110 if index < 2 else 82, 1)
    for x, color, phase in [(150, TEAL, 0), (600, TEAL, 0.7), (1050, TEAL, 1.4)]:
        y = 69 + sin(t * 0.9 + phase) * 3
        glow(image, x, int(y), color, 5 + int((sin(t * 1.4 + phase) + 1) * 1.2))
    return image.convert("RGB").quantize(colors=96, method=Image.Quantize.MEDIANCUT)


def save_gif(path: Path, frames, duration: int):
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=duration, loop=0, disposal=2, optimize=True)


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    save_gif(ASSETS / "profile-signal-field.gif", [hero_frame(frame) for frame in range(24)], 82)
    save_gif(ASSETS / "route-pulse-strip.gif", [strip_frame(frame) for frame in range(20)], 88)
    print(ASSETS / "profile-signal-field.gif")
    print(ASSETS / "route-pulse-strip.gif")


if __name__ == "__main__":
    main()
