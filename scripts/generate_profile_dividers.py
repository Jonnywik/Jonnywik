"""Render compact Signal section dividers.

Run: python scripts/generate_profile_dividers.py

Uses the self-hosted Anton + Chakra Petch fonts in assets/fonts so the scheduled
telemetry refresh and manual runs produce the same blue/cyan identity.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
FONTS = ASSETS / "fonts"
WIDTH, HEIGHT = 1200, 128

# Signal palette (DESIGN.md / tokens.json)
NAVY = (7, 14, 37)
BORDER = (52, 86, 127)
BLUE = (149, 186, 255)
CYAN = (136, 236, 255)
TEXT = (240, 245, 255)
MUTED = (184, 204, 232)
NODES = (770, 961, 1152)
TRACE_Y = 64


def font(name, size):
    candidate = FONTS / name
    if candidate.exists():
        return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default(size=size)


def header(title, summary, accent):
    image = Image.new("RGBA", (WIDTH, HEIGHT), (*NAVY, 255))
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    # hairline rules keep this a divider, not a banner.
    draw.line((0, 1, WIDTH, 1), fill=(*BORDER, 255), width=2)
    draw.line((0, HEIGHT - 2, WIDTH, HEIGHT - 2), fill=(*BORDER, 255), width=2)
    draw.rectangle((40, 30, 44, 98), fill=(*accent, 255))
    draw.text((64, 30), title, font=font("anton-400.ttf", 42), fill=(*TEXT, 255))
    draw.text((66, 86), summary, font=font("chakrapetch-400.ttf", 21), fill=(*MUTED, 255))
    image = Image.alpha_composite(image, layer)

    # thin signal trace on the right: a restrained accent, not a bulky graphic.
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.line((NODES[0], TRACE_Y, NODES[-1], TRACE_Y), fill=(*BORDER, 255), width=2)
    for index, x in enumerate(NODES):
        radius = 4 if index == 1 else 3
        dot = CYAN if index == 1 else accent
        glow_draw.ellipse((x - radius * 3, TRACE_Y - radius * 3, x + radius * 3, TRACE_Y + radius * 3), fill=(*dot, 120))
    image = Image.alpha_composite(image, glow.filter(ImageFilter.GaussianBlur(7)))
    crisp = ImageDraw.Draw(image)
    for index, x in enumerate(NODES):
        radius = 4 if index == 1 else 3
        dot = CYAN if index == 1 else accent
        crisp.ellipse((x - radius, TRACE_Y - radius, x + radius, TRACE_Y + radius), fill=(*dot, 255), outline=(*CYAN, 255), width=1)
    return image.convert("RGB")


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    # Short numbered kickers so the divider never duplicates the markdown heading below it.
    dividers = [
        ("divider-decision-trace.gif", "01 / WORK", "Selected systems, previews, and source", CYAN),
        ("divider-method-state.gif", "02 / METHOD", "Engineering focus with supporting interests", BLUE),
        ("divider-telemetry.gif", "03 / TELEMETRY", "Contribution snapshot and public activity", CYAN),
        ("divider-source-first.gif", "04 / LINKS", "Portfolio, source, and repositories", BLUE),
    ]
    for name, title, summary, accent in dividers:
        path = ASSETS / name
        header(title, summary, accent).save(path, format="GIF", optimize=True)
        print(path)


if __name__ == "__main__":
    main()
