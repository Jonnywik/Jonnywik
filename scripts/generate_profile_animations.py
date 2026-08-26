from math import cos, pi, sin
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
TEAL = (45, 212, 191)
ORANGE = (251, 146, 60)
VIOLET = (167, 139, 250)
WHITE = (220, 248, 243)


def route_points(width: int, baseline: float, amplitude: float, phase: float, lift: float, t: float):
    points = []
    for x in range(-40, width + 42, 5):
        progress = x / width
        wave = sin(progress * pi * 2.25 + phase + t * 0.22) * amplitude
        rising = -max(0, progress - 0.47) * lift
        micro = sin(progress * pi * 6 + phase + t * 0.65) * 3.2
        points.append((x, baseline + wave + rising + micro))
    return points


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

    specs = [
        (282, 38, 0.05, 226, TEAL, 168),
        (311, 42, 0.42, 238, TEAL, 128),
        (340, 45, 0.78, 246, TEAL, 108),
        (382, 25, 1.22, 282, VIOLET, 120),
        (402, 20, 1.72, 312, ORANGE, 105),
    ]
    routes = []
    for line_index, (baseline, amp, phase, lift, color, opacity) in enumerate(specs):
        vertical = sin(t * 1.15 + line_index * 0.92) * (7 + line_index)
        points = route_points(width, baseline + vertical, amp, phase, lift, t)
        routes.append(points)
        draw_dashed_route(draw, points, color, int(frame * 1.4 + line_index * 3), opacity, 2 if line_index < 3 else 1)

    node_indices = [(0, 142, TEAL, 10), (1, 183, TEAL, 7), (3, 216, ORANGE, 8), (2, 221, VIOLET, 7)]
    for route_index, point_index, color, radius in node_indices:
        x, y = routes[route_index][min(point_index, len(routes[route_index]) - 1)]
        glow(image, int(x), int(y), color, radius)

    particle_draw = ImageDraw.Draw(image, "RGBA")
    for particle_index in range(22):
        route = routes[particle_index % len(routes)]
        location = int((particle_index * 31 + frame * (3 + particle_index % 4)) % (len(route) - 1))
        x, y = route[location]
        rise = sin(t * 1.8 + particle_index) * 5
        color = TEAL if particle_index % 5 else ORANGE if particle_index % 7 else VIOLET
        radius = 1 + particle_index % 2
        particle_draw.ellipse((x - radius, y + rise - radius, x + radius, y + rise + radius), fill=(*color, 185))

    return image.convert("P", palette=Image.Palette.ADAPTIVE, colors=128)


def strip_frame(frame: int, width: int = 1200, height: int = 138) -> Image.Image:
    t = frame / 20 * pi * 2
    image = Image.new("RGBA", (width, height), (9, 13, 18, 255))
    draw = ImageDraw.Draw(image, "RGBA")
    for index, color in enumerate((TEAL, TEAL, VIOLET, ORANGE)):
        baseline = 76 + index * 9
        points = route_points(width, baseline + sin(t + index) * 5, 14 + index * 3, 0.4 * index, 66, t)
        draw_dashed_route(draw, points, color, frame + index * 2, 142 if index < 2 else 110, 1)
        spot = points[int((frame * 8 + index * 79) % len(points))]
        draw.ellipse((spot[0] - 2, spot[1] - 2, spot[0] + 2, spot[1] + 2), fill=(*color, 230))
    return image.convert("P", palette=Image.Palette.ADAPTIVE, colors=96)


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
