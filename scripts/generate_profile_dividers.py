from math import pi, sin
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
WIDTH, HEIGHT, FRAMES = 1200, 128, 30

INK = (8, 14, 20)
GRID = (34, 53, 63)
TEAL = (45, 212, 191)
MINT = (169, 249, 236)
AMBER = (251, 188, 93)
VIOLET = (167, 139, 250)
WHITE = (226, 245, 242)
SLATE = (138, 168, 177)


def font(name, size):
    candidates = [
        f"/usr/share/fonts/truetype/dejavu/{name}",
        f"/usr/share/fonts/truetype/liberation2/{name}",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


FONT_TITLE = font("DejaVuSans-Bold.ttf", 20)
FONT_META = font("DejaVuSansMono.ttf", 10)
FONT_LABEL = font("DejaVuSans-Bold.ttf", 9)


def cubic(start, control_one, control_two, end, steps=56):
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
    index = max(0, min(len(points) - 1, int((progress % 1) * (len(points) - 1))))
    return points[index]


def base_frame(frame, primary=TEAL, secondary=VIOLET):
    image = Image.new("RGBA", (WIDTH, HEIGHT), (*INK, 255))
    grid = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(grid)
    for x in range(0, WIDTH + 1, 60):
        draw.line((x, 0, x, HEIGHT), fill=(*GRID, 54), width=1)
    for y in range(0, HEIGHT + 1, 32):
        draw.line((0, y, WIDTH, y), fill=(*GRID, 44), width=1)
    draw.rectangle((1, 1, WIDTH - 2, HEIGHT - 2), outline=(*WHITE, 30), width=1)
    image.alpha_composite(grid)

    t = frame / FRAMES * pi * 2
    haze = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(haze)
    draw.ellipse((280 + sin(t) * 34, -82, 720 + sin(t) * 34, 184), fill=(*primary, 22))
    draw.ellipse((735 - sin(t * 0.72) * 28, -32, 1140 - sin(t * 0.72) * 28, 160), fill=(*secondary, 16))
    draw.ellipse((862, 50 + sin(t * 1.15) * 7, 1185, 188 + sin(t * 1.15) * 7), fill=(*AMBER, 9))
    image.alpha_composite(haze.filter(ImageFilter.GaussianBlur(50)))
    return image


def draw_copy(image, index, title, summary, accent):
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.rectangle((42, 23, 46, 104), fill=(*accent, 210))
    draw.text((62, 24), index, font=FONT_META, fill=(*accent, 245))
    draw.text((62, 43), title, font=FONT_TITLE, fill=(*WHITE, 248))
    draw.text((62, 74), summary, font=FONT_META, fill=(*SLATE, 246))
    image.alpha_composite(layer)


def draw_route(image, points, color, opacity=126, width=2):
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).line(points, fill=(*color, opacity), width=width, joint="curve")
    image.alpha_composite(layer)


def draw_packet(image, route, progress, color, size=3):
    wake = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(wake)
    for offset in range(9, -1, -1):
        x, y = point_on_route(route, progress - offset * 0.016)
        radius = max(1, size - offset // 3)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, 22 + (9 - offset) * 22))
    image.alpha_composite(wake.filter(ImageFilter.GaussianBlur(3)))
    crisp = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(crisp)
    x, y = point_on_route(route, progress)
    draw.ellipse((x - size, y - size, x + size, y + size), fill=(*color, 248), outline=(*WHITE, 205), width=1)
    image.alpha_composite(crisp)


def glow_node(image, x, y, color, frame, phase=0, radius=5, label=None):
    pulse = int((sin(frame / FRAMES * pi * 2 * 1.35 + phase) + 1) * 2)
    aura = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(aura)
    draw.ellipse((x - radius * 2 - pulse, y - radius * 2 - pulse, x + radius * 2 + pulse, y + radius * 2 + pulse), fill=(*color, 78))
    image.alpha_composite(aura.filter(ImageFilter.GaussianBlur(radius * 2)))
    crisp = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(crisp)
    ring = radius + 3 + pulse
    draw.ellipse((x - ring, y - ring, x + ring, y + ring), outline=(*color, 118), width=1)
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, 238), outline=(*WHITE, 200), width=1)
    if label:
        draw.text((x + 12, y - 5), label, font=FONT_LABEL, fill=(*color, 238))
    image.alpha_composite(crisp)


def quantize(image):
    return image.convert("RGB").quantize(colors=112, method=Image.Quantize.MEDIANCUT)


def work_map_frame(frame):
    image = base_frame(frame, TEAL, VIOLET)
    draw_copy(image, "01 / WORK MAP", "FEATURED SYSTEMS", "INTERFACES  /  EVIDENCE  /  SOURCE", TEAL)
    trunk = chain(((340, 93), (470, 105), (510, 38), (635, 64)))
    system = chain(((635, 64), (760, 40), (845, 24), (1078, 28)))
    evidence = chain(((635, 64), (760, 77), (882, 65), (1078, 64)))
    source = chain(((635, 64), (754, 93), (882, 106), (1078, 100)))
    draw_route(image, trunk, TEAL, 165, 2)
    draw_route(image, system, MINT, 138, 2)
    draw_route(image, evidence, AMBER, 142, 2)
    draw_route(image, source, VIOLET, 142, 2)
    for route, progress, color, size in [
        (trunk, frame / FRAMES * 0.74 + 0.05, TEAL, 3),
        (system, frame / FRAMES * 0.53 + 0.28, MINT, 2),
        (evidence, frame / FRAMES * 0.61 + 0.62, AMBER, 3),
        (source, frame / FRAMES * 0.47 + 0.44, VIOLET, 2),
    ]:
        draw_packet(image, route, progress, color, size)
    glow_node(image, 635, 64, TEAL, frame, 0, 5)
    glow_node(image, 1078, 28, MINT, frame, 0.7, 4, "SYSTEM")
    glow_node(image, 1078, 64, AMBER, frame, 1.3, 4, "EVIDENCE")
    glow_node(image, 1078, 100, VIOLET, frame, 2.0, 4, "SOURCE")
    return quantize(image)


def decision_trace_frame(frame):
    image = base_frame(frame, AMBER, VIOLET)
    draw_copy(image, "02 / DECISION TRACE", "EVIDENCE RECORDS", "ARCHITECTURE  /  BOUNDARIES  /  CONTEXT", AMBER)
    route = chain(((340, 70), (470, 31), (560, 109), (702, 66)), ((702, 66), (776, 46), (812, 51), (862, 63)))
    draw_route(image, route, TEAL, 146, 2)
    scan = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(scan)
    for index, (x, y, color, alpha) in enumerate([(808, 28, VIOLET, 80), (830, 38, TEAL, 120), (852, 48, AMBER, 178)]):
        draw.rounded_rectangle((x, y, x + 270, y + 46), radius=5, outline=(*color, alpha), width=1)
        draw.rectangle((x + 17, y + 13, x + 178, y + 15), fill=(*MINT, alpha))
        draw.rectangle((x + 17, y + 27, x + 92 + index * 26, y + 29), fill=(*color, alpha))
    image.alpha_composite(scan)
    draw_packet(image, route, frame / FRAMES * 0.76 + 0.08, TEAL, 3)
    draw_packet(image, route, frame / FRAMES * 0.49 + 0.56, AMBER, 2)
    glow_node(image, 862, 63, AMBER, frame, 0.4, 5, "VERIFY")
    glow_node(image, 1098, 94, VIOLET, frame, 1.1, 4, "TRACE")
    return quantize(image)


def method_state_frame(frame):
    image = base_frame(frame, VIOLET, TEAL)
    draw_copy(image, "03 / METHOD + STATE", "ACTIVE PRINCIPLES", "CLARITY  /  RESILIENCE  /  BOUNDARIES", VIOLET)
    source = chain(((340, 65), (460, 64), (540, 64), (630, 64)))
    clarity = chain(((630, 64), (735, 51), (780, 27), (922, 27)))
    resilience = chain(((630, 64), (738, 64), (820, 64), (1010, 64)))
    boundary = chain(((630, 64), (738, 78), (812, 101), (1095, 101)))
    draw_route(image, source, MINT, 172, 2)
    draw_route(image, clarity, TEAL, 145, 2)
    draw_route(image, resilience, VIOLET, 145, 2)
    draw_route(image, boundary, AMBER, 145, 2)
    for route, progress, color, size in [
        (source, frame / FRAMES * 0.73 + 0.06, MINT, 3),
        (clarity, frame / FRAMES * 0.49 + 0.38, TEAL, 2),
        (resilience, frame / FRAMES * 0.63 + 0.18, VIOLET, 3),
        (boundary, frame / FRAMES * 0.45 + 0.67, AMBER, 2),
    ]:
        draw_packet(image, route, progress, color, size)
    glow_node(image, 630, 64, MINT, frame, 0, 5)
    glow_node(image, 922, 27, TEAL, frame, 0.5, 4, "CLARITY")
    glow_node(image, 1010, 64, VIOLET, frame, 1.1, 4, "RESILIENCE")
    glow_node(image, 1095, 101, AMBER, frame, 1.7, 4, "BOUNDARY")
    return quantize(image)


def telemetry_frame(frame):
    image = base_frame(frame, TEAL, VIOLET)
    draw_copy(image, "04 / TELEMETRY", "PUBLIC SIGNALS", "REPOSITORIES  /  ACTIVITY  /  STACK", TEAL)
    rail = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(rail)
    y = 67
    draw.line((340, y, 1120, y), fill=(*TEAL, 142), width=2)
    for index, x in enumerate(range(380, 1121, 48)):
        height = 10 if index % 4 == 0 else 5
        color = VIOLET if index % 5 == 0 else MINT
        draw.line((x, y - height, x, y + height), fill=(*color, 92), width=1)
    for x, color in [(534, TEAL), (725, VIOLET), (918, AMBER), (1080, MINT)]:
        draw.rectangle((x - 22, 92, x + 22, 95), fill=(*color, 72))
    image.alpha_composite(rail)
    route = [(340, y), (1120, y)]
    draw_packet(image, route, frame / FRAMES * 0.82 + 0.02, AMBER, 3)
    draw_packet(image, route, frame / FRAMES * 0.58 + 0.39, VIOLET, 2)
    for phase, (x, color, label) in enumerate([(534, TEAL, "REPOS"), (725, VIOLET, "ACTIVITY"), (918, AMBER, "STACK"), (1080, MINT, "PUBLIC")]):
        glow_node(image, x, y, color, frame, phase * 0.62, 4, label)
    return quantize(image)


def source_first_frame(frame):
    image = base_frame(frame, VIOLET, AMBER)
    draw_copy(image, "05 / SOURCE-FIRST", "TRACE TO CODE", "PROJECT STORY  →  PUBLIC IMPLEMENTATION", VIOLET)
    route_a = chain(((465, 83), (588, 102), (670, 34), (800, 65)))
    route_b = chain(((800, 65), (884, 94), (954, 47), (1084, 58)))
    draw_route(image, route_a, TEAL, 158, 2)
    draw_route(image, route_b, VIOLET, 165, 2)
    symbols = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(symbols)
    draw.line((395, 40, 370, 64, 395, 88), fill=(*MINT, 172), width=2)
    draw.line((429, 40, 454, 64, 429, 88), fill=(*MINT, 172), width=2)
    draw.line((465, 34, 442, 94), fill=(*TEAL, 158), width=2)
    draw.polygon([(1110, 58), (1082, 42), (1082, 74)], outline=(*AMBER, 218), fill=(*AMBER, 72))
    image.alpha_composite(symbols)
    draw_packet(image, route_a, frame / FRAMES * 0.67 + 0.09, TEAL, 3)
    draw_packet(image, route_b, frame / FRAMES * 0.56 + 0.48, VIOLET, 2)
    glow_node(image, 465, 83, TEAL, frame, 0, 4, "CODE")
    glow_node(image, 800, 65, VIOLET, frame, 0.8, 5, "TRACE")
    glow_node(image, 1084, 58, AMBER, frame, 1.5, 5, "OPEN")
    return quantize(image)


def save_gif(name, renderer):
    frames = [renderer(frame) for frame in range(FRAMES)]
    frames[0].save(ASSETS / name, save_all=True, append_images=frames[1:], duration=82, loop=0, disposal=2, optimize=True)


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
