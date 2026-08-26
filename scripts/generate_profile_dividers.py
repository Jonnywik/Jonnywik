from math import sin, pi
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
WIDTH, HEIGHT = 1200, 128
FRAMES = 24

INK = (8, 14, 20)
GRID = (34, 53, 63)
TEAL = (45, 212, 191)
MINT = (169, 249, 236)
AMBER = (251, 188, 93)
WHITE = (220, 248, 243)


def cubic(start, control_one, control_two, end, steps=52):
    points = []
    for index in range(steps + 1):
        ratio = index / steps
        inverse = 1 - ratio
        points.append(
            (
                inverse**3 * start[0]
                + 3 * inverse**2 * ratio * control_one[0]
                + 3 * inverse * ratio**2 * control_two[0]
                + ratio**3 * end[0],
                inverse**3 * start[1]
                + 3 * inverse**2 * ratio * control_one[1]
                + 3 * inverse * ratio**2 * control_two[1]
                + ratio**3 * end[1],
            )
        )
    return points


def chain(*segments):
    points = []
    for index, segment in enumerate(segments):
        curve = cubic(*segment)
        points.extend(curve if index == 0 else curve[1:])
    return points


def point_on_route(points, progress):
    location = max(0, min(len(points) - 1, int((progress % 1) * (len(points) - 1))))
    return points[location]


def base_frame():
    image = Image.new("RGBA", (WIDTH, HEIGHT), (*INK, 255))
    grid = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(grid)
    for x in range(0, WIDTH + 1, 60):
        draw.line((x, 0, x, HEIGHT), fill=(*GRID, 52), width=1)
    for y in range(0, HEIGHT + 1, 32):
        draw.line((0, y, WIDTH, y), fill=(*GRID, 42), width=1)
    draw.rectangle((1, 1, WIDTH - 2, HEIGHT - 2), outline=(*WHITE, 24), width=1)
    image.alpha_composite(grid)

    haze = Image.new("RGBA", image.size, (0, 0, 0, 0))
    haze_draw = ImageDraw.Draw(haze)
    haze_draw.ellipse((330, -82, 940, 192), fill=(*TEAL, 18))
    image.alpha_composite(haze.filter(ImageFilter.GaussianBlur(58)))
    return image


def draw_routes(image, routes, highlighted=0):
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for index, points in enumerate(routes):
        color = MINT if index == highlighted else TEAL
        opacity = 132 if index == highlighted else 80
        width = 2 if index == highlighted else 1
        draw.line(points, fill=(*color, opacity), width=width, joint="curve")
    image.alpha_composite(layer)


def glow_node(image, x, y, color=TEAL, radius=5):
    aura = Image.new("RGBA", image.size, (0, 0, 0, 0))
    aura_draw = ImageDraw.Draw(aura)
    aura_draw.ellipse((x - radius * 2, y - radius * 2, x + radius * 2, y + radius * 2), fill=(*color, 72))
    image.alpha_composite(aura.filter(ImageFilter.GaussianBlur(radius * 2)))
    crisp = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(crisp)
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, 230), outline=(*WHITE, 185), width=1)
    image.alpha_composite(crisp)


def draw_packet(image, route, progress, color=TEAL, size=3):
    wake = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(wake)
    for offset in range(8, -1, -1):
        x, y = point_on_route(route, progress - offset * 0.018)
        radius = max(1, size - offset // 3)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, 22 + (8 - offset) * 24))
    image.alpha_composite(wake.filter(ImageFilter.GaussianBlur(3)))
    crisp = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(crisp)
    x, y = point_on_route(route, progress)
    draw.ellipse((x - size, y - size, x + size, y + size), fill=(*color, 245), outline=(*WHITE, 195), width=1)
    image.alpha_composite(crisp)


def work_map_frame(frame):
    image = base_frame()
    t = frame / FRAMES * pi * 2
    trunk = chain(((50, 92), (260, 104), (380, 29), (560, 65)))
    top = chain(((560, 65), (740, 40), (865, 24), (1110, 27)))
    middle = chain(((560, 65), (734, 79), (880, 63), (1110, 63)))
    lower = chain(((560, 65), (730, 98), (892, 106), (1110, 99)))
    routes = [trunk, top, middle, lower]
    draw_routes(image, routes, highlighted=0)
    for route, progress, size in [(trunk, frame / FRAMES * 0.52 + 0.10, 3), (top, frame / FRAMES * 0.42 + 0.55, 2), (middle, frame / FRAMES * 0.46 + 0.26, 3), (lower, frame / FRAMES * 0.38 + 0.72, 2)]:
        draw_packet(image, route, progress, TEAL, size)
    glow_node(image, 560, int(65 + sin(t) * 1.5), TEAL, 5)
    glow_node(image, 1110, 27, MINT, 4)
    glow_node(image, 1110, 63, AMBER, 4)
    glow_node(image, 1110, 99, TEAL, 4)
    return image.convert("RGB").quantize(colors=88, method=Image.Quantize.MEDIANCUT)


def decision_trace_frame(frame):
    image = base_frame()
    t = frame / FRAMES * pi * 2
    route = chain(((70, 68), (250, 32), (416, 111), (605, 66)), ((605, 66), (713, 43), (776, 56), (835, 64)))
    draw_routes(image, [route])
    records = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(records)
    for index, (x, y, alpha) in enumerate([(780, 28, 52), (802, 38, 74), (824, 48, 112)]):
        draw.rounded_rectangle((x, y, x + 250, y + 46), radius=4, outline=(*TEAL, alpha), width=1)
        draw.line((x + 18, y + 16, x + 175, y + 16), fill=(*MINT, alpha), width=1)
        draw.line((x + 18, y + 29, x + 112 + index * 18, y + 29), fill=(*TEAL, alpha), width=1)
    image.alpha_composite(records)
    draw_packet(image, route, frame / FRAMES * 0.61 + 0.08, TEAL, 3)
    draw_packet(image, route, frame / FRAMES * 0.42 + 0.56, MINT, 2)
    glow_node(image, 835, int(64 + sin(t) * 1.5), TEAL, 5)
    glow_node(image, 1072, 94, AMBER, 4)
    return image.convert("RGB").quantize(colors=88, method=Image.Quantize.MEDIANCUT)


def method_state_frame(frame):
    image = base_frame()
    t = frame / FRAMES * pi * 2
    source = chain(((95, 65), (232, 64), (347, 64), (470, 64)))
    upper = chain(((470, 64), (620, 52), (685, 28), (850, 28)))
    centre = chain(((470, 64), (625, 64), (708, 64), (965, 64)))
    lower = chain(((470, 64), (620, 76), (700, 100), (1080, 100)))
    routes = [source, upper, centre, lower]
    draw_routes(image, routes, highlighted=1)
    for route, progress, size in [(source, frame / FRAMES * 0.56 + 0.08, 3), (upper, frame / FRAMES * 0.40 + 0.42, 2), (centre, frame / FRAMES * 0.46 + 0.21, 3), (lower, frame / FRAMES * 0.38 + 0.70, 2)]:
        draw_packet(image, route, progress, TEAL, size)
    glow_node(image, 470, int(64 + sin(t) * 1.4), TEAL, 5)
    glow_node(image, 850, 28, MINT, 4)
    glow_node(image, 965, 64, TEAL, 4)
    glow_node(image, 1080, 100, AMBER, 4)
    return image.convert("RGB").quantize(colors=88, method=Image.Quantize.MEDIANCUT)


def telemetry_frame(frame):
    image = base_frame()
    rail = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(rail)
    y = 67
    draw.line((80, y, 1120, y), fill=(*TEAL, 118), width=2)
    for index, x in enumerate(range(120, 1121, 80)):
        tick_height = 8 if index % 3 == 0 else 4
        draw.line((x, y - tick_height, x, y + tick_height), fill=(*MINT, 78), width=1)
    image.alpha_composite(rail)
    route = [(80, y), (1120, y)]
    for progress, size in [(frame / FRAMES * 0.62 + 0.06, 3), (frame / FRAMES * 0.43 + 0.48, 2)]:
        draw_packet(image, route, progress, TEAL, size)
    for index, (x, color) in enumerate([(280, TEAL), (580, MINT), (820, AMBER), (1030, TEAL)]):
        glow_node(image, x, int(y + sin(frame / FRAMES * pi * 2 + index) * 1.2), color, 4)
    return image.convert("RGB").quantize(colors=72, method=Image.Quantize.MEDIANCUT)


def source_first_frame(frame):
    image = base_frame()
    t = frame / FRAMES * pi * 2
    route = chain(((258, 82), (430, 103), (566, 33), (740, 66)), ((740, 66), (850, 94), (927, 46), (1086, 58)))
    draw_routes(image, [route])
    symbols = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(symbols)
    draw.line((116, 40, 92, 64, 116, 88), fill=(*MINT, 122), width=2)
    draw.line((150, 40, 174, 64, 150, 88), fill=(*MINT, 122), width=2)
    draw.line((188, 34, 164, 94), fill=(*TEAL, 112), width=2)
    draw.polygon([(1100, 58), (1075, 44), (1075, 72)], outline=(*AMBER, 188), fill=(*AMBER, 54))
    image.alpha_composite(symbols)
    draw_packet(image, route, frame / FRAMES * 0.56 + 0.08, TEAL, 3)
    draw_packet(image, route, frame / FRAMES * 0.41 + 0.52, MINT, 2)
    glow_node(image, 258, int(82 + sin(t) * 1.2), TEAL, 4)
    glow_node(image, 1086, 58, AMBER, 5)
    return image.convert("RGB").quantize(colors=88, method=Image.Quantize.MEDIANCUT)


def save_gif(name, renderer):
    frames = [renderer(frame) for frame in range(FRAMES)]
    frames[0].save(ASSETS / name, save_all=True, append_images=frames[1:], duration=92, loop=0, disposal=2, optimize=True)


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    for name, renderer in [
        ("divider-work-map.gif", work_map_frame),
        ("divider-decision-trace.gif", decision_trace_frame),
        ("divider-method-state.gif", method_state_frame),
        ("divider-telemetry.gif", telemetry_frame),
        ("divider-source-first.gif", source_first_frame),
    ]:
        save_gif(name, renderer)
        print(ASSETS / name)


if __name__ == "__main__":
    main()
