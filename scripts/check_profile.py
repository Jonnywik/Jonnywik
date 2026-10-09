"""Run: python scripts/check_profile.py (requires the existing Pillow renderer dependency).

Regression checks for the Signal identity profile README and its owned assets.
"""
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_profile_dividers as dividers
import generate_profile_telemetry as telemetry

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
readme = (ROOT / "README.md").read_text(encoding="utf-8")

# --- README shape ---------------------------------------------------------
assert len(readme.splitlines()) < 100
assert readme.count("https://jonnywik.github.io/") == 2

# --- Public identity: focus vs supporting interests -----------------------
assert "# Mikael Lim" in readme
assert "BSIT at PLM" in readme
assert "Software engineering is my focus" in readme
assert "supporting interests" in readme
assert "Open to relevant opportunities" in readme
assert "{{" not in readme and "TODO" not in readme and "Lorem" not in readme
for placeholder in ["[Your ", "Your Name", "role placeholder"]:
    assert placeholder not in readme

# --- Honest demo boundaries ----------------------------------------------
assert "not a certified emergency-service deployment" in readme
assert "not live employee information" in readme
assert "original concept illustration, not a product screenshot" in readme

# --- Contribution summary is compact and visible (not a collapsed section) -
assert readme.count(telemetry.START) == readme.count(telemetry.END) == 1
assert readme.count("<details>") == readme.count("</details>") == 0
import re
assert re.search(r"\| \d+ \| \d+ \| \d+ \|", readme)
assert "Real GitHub GraphQL snapshot · window" in readme

# --- Required repository links -------------------------------------------
for repo in ["EnvScie-CommandCenter", "employee-management-dashboard", "ingritializer", "transit-planner", "Jonnywik.github.io"]:
    assert f"https://github.com/Jonnywik/{repo}" in readme

# --- Retired Signal v1/v2/v3 assets and slogans must be gone --------------
for gone in [
    "divider-work-map.gif",
    "profile-signal-field",
    "portfolio-command-center.svg",
    "route-pulse-strip",
    "route-node-pulse",
    "mikael-lim-portrait",
    "recent-activity-feed",
    "SIGNAL NODES",
    "QUICK TRACE",
]:
    assert gone not in readme, gone

# --- Every referenced raw asset exists locally ---------------------------
raw = "https://raw.githubusercontent.com/Jonnywik/Jonnywik/main/assets/"
referenced = {line.split(raw, 1)[1].split(")")[0] for line in readme.splitlines() if raw in line}
assert referenced, "no raw assets referenced"
for name in referenced:
    assert (ASSETS / name).exists(), name

# --- Telemetry renderer produces a real GraphQL snapshot card -------------
sample = {
    "repositories": {"totalCount": 11},
    "contributionsCollection": {
        "startedAt": "2025-10-04T16:00:00Z",
        "endedAt": "2026-10-09T15:59:59Z",
        "totalCommitContributions": 202,
        "contributionCalendar": {"totalContributions": 215},
    },
}
data = telemetry.metrics(sample)
assert data == {"calendar": 215, "commits": 202, "repos": 11, "window": "Oct 4, 2025 – Oct 9, 2026"}, data
block = telemetry.markdown_block(data)
assert telemetry.START in block and telemetry.END in block
assert "| 215 | 202 | 11 |" in block and "Oct 4, 2025" in block
with tempfile.TemporaryDirectory() as tmp, patch.object(telemetry, "ASSETS", Path(tmp)):
    with Image.open(telemetry.render(data)) as card:
        assert card.size == (1200, 460)

# --- Divider renderer uses local fonts and fits its copy ------------------
for name in ["anton-400.ttf", "chakrapetch-400.ttf", "chakrapetch-500.ttf", "chakrapetch-600.ttf"]:
    assert (ASSETS / "fonts" / name).exists(), name
for name in ["anton-LICENSE.txt", "chakrapetch-LICENSE.txt"]:
    assert (ASSETS / "fonts" / name).exists(), name
measure = ImageDraw.Draw(Image.new("RGB", (1200, 128)))
assert measure.textlength("Engineering focus with supporting interests", font=dividers.font("chakrapetch-400.ttf", 21)) < 1080

# --- Asset inventory: sizes and identity ----------------------------------
with Image.open(ASSETS / "profile-banner.png") as banner:
    assert banner.size == (1200, 400), banner.size
for name in ["divider-decision-trace.gif", "divider-method-state.gif", "divider-telemetry.gif", "divider-source-first.gif"]:
    with Image.open(ASSETS / name) as divider:
        assert divider.size == (1200, 128), (name, divider.size)
for name, size in [("github-activity-card.png", (1200, 460)), ("command-center-demo.png", (1440, 810)), ("employee-dashboard-demo.png", (2560, 1440))]:
    with Image.open(ASSETS / name) as image:
        assert image.size == size, (name, image.size)

print("PASS: Signal README identity, honest boundaries, compact dated contribution summary, repository links, retired-asset cleanup, local fonts, and 1200-wide asset set.")
