from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 1200, 250
BACKGROUND = "#090d12"
PANEL = "#101820"
LINE = "#263440"
MUTED = "#8d9ca8"
TEXT = "#dce8ed"
TEAL = "#2dd4bf"
ORANGE = "#fb923c"
VIOLET = "#a78bfa"

METRICS = [
    ("PUBLIC REPOSITORIES", "8", TEAL),
    ("2026 CONTRIBUTIONS", "69", ORANGE),
    ("FEATURED SYSTEMS", "3", VIOLET),
    ("FOLLOWERS", "1", TEAL),
]


def font(path: str, size: int):
    return ImageFont.truetype(path, size)


root = Path(__file__).resolve().parents[1]
output = root / "assets" / "github-activity-card.png"
output.parent.mkdir(parents=True, exist_ok=True)

display = font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
display_bold = font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 31)
mono = font("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
mono_small = font("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 10)

image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
draw = ImageDraw.Draw(image)

for x in range(0, WIDTH, 48):
    draw.line((x, 0, x, HEIGHT), fill="#121d25", width=1)
for y in range(0, HEIGHT, 48):
    draw.line((0, y, WIDTH, y), fill="#121d25", width=1)

draw.rounded_rectangle((20, 20, WIDTH - 20, HEIGHT - 20), radius=12, outline=LINE, width=1, fill=PANEL)
draw.text((48, 47), "GITHUB / PUBLIC SIGNAL", font=mono, fill=TEAL)
draw.text((48, 74), "Activity snapshot", font=display, fill=TEXT)
draw.text((48, 102), "Self-hosted profile telemetry · refreshed on demand", font=mono_small, fill=MUTED)

route = [(430, 196), (520, 156), (615, 184), (705, 123), (805, 153), (890, 86), (1010, 110), (1135, 54)]
draw.line(route, fill="#1c5a58", width=2, joint="curve")
for offset, color in [(0, TEAL), (15, "#1a4248"), (29, "#1c3748")]:
    shifted = [(x, y - offset) for x, y in route]
    draw.line(shifted, fill=color, width=1, joint="curve")

start_x = 430
card_width = 172
for index, (label, value, accent) in enumerate(METRICS):
    x = start_x + index * card_width
    draw.rounded_rectangle((x, 38, x + 152, 151), radius=8, fill="#0b1117", outline=LINE, width=1)
    draw.rectangle((x, 38, x + 4, 151), fill=accent)
    draw.ellipse((x + 22, 56, x + 30, 64), fill=accent)
    draw.text((x + 42, 53), label, font=mono_small, fill=MUTED)
    draw.text((x + 21, 81), value, font=display_bold, fill=TEXT)
    draw.text((x + 21, 124), "PUBLIC DATA", font=mono_small, fill=accent)

for x, y, color in [(705, 181, TEAL), (891, 88, ORANGE), (1135, 55, VIOLET)]:
    draw.ellipse((x - 10, y - 10, x + 10, y + 10), outline=color, width=1)
    draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=color)

draw.text((48, 200), f"SNAPSHOT DATE / {date.today().isoformat()}  ·  SOURCE / GITHUB PUBLIC API", font=mono_small, fill=MUTED)
draw.text((1011, 200), "JONNYWIK / COMMAND CENTER", font=mono_small, fill=TEAL)

image.save(output, "PNG", optimize=True)
print(output)
