"""Run: python scripts/check_profile.py (requires the existing Pillow renderer dependency)."""
import tempfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw
import generate_profile_animations as hero
import generate_profile_dividers as dividers
import generate_recent_activity_feed as feed

ROOT = Path(__file__).resolve().parents[1]
readme = (ROOT / "README.md").read_text(encoding="utf-8")
assert len(readme.splitlines()) < 100
assert readme.count("https://jonnywik.github.io/") == 2
assert "SIGNAL NODES" not in readme and "QUICK TRACE" not in readme
assert readme.count("<details>") == readme.count("</details>") == 1
assert readme.count(feed.START) == readme.count(feed.END) == 1
assert "not a certified emergency-service deployment" in readme

# Deliberately unordered test fixtures: newest push wins, full branch survives.
events = [
    {"type": "PushEvent", "repo": {"name": "test/project"}, "created_at": "2026-01-01T00:00:00Z", "payload": {"head": "a" * 40, "ref": "refs/heads/main"}},
    {"type": "PushEvent", "repo": {"name": "test/project"}, "created_at": "2026-01-02T00:00:00Z", "payload": {"head": "b" * 40, "ref": "refs/heads/feature/readable-profile"}},
]
with patch.object(feed, "github_json", return_value=events):
    pushes = feed.recent_pushes("test")
assert len(pushes) == 1 and pushes[0]["sha"] == "bbbbbbb"
assert pushes[0]["branch"] == "feature/readable-profile"
block = feed.markdown_block(pushes, [])
assert "2026-01-02 UTC" in block and "<details>" not in block
assert "event feed" in feed.markdown_block([], [])

# Exercise empty and maximum-row layouts without replacing published real data.
with tempfile.TemporaryDirectory(dir=ROOT) as tmp, patch.object(feed, "ASSETS", Path(tmp)):
    with Image.open(feed.render([], [])) as empty:
        assert empty.size == (1200, 301)
    rows = [dict(pushes[0], repo="test/" + "long-name-" * 20) for _ in range(4)]
    with Image.open(feed.render(rows, [])) as full:
        assert full.size == (1200, 460)

assets = [
    "profile-signal-field-fallback.png", "divider-method-state.gif",
    "divider-decision-trace.gif", "divider-telemetry.gif",
    "github-activity-card.png", "recent-activity-feed.png",
    "divider-source-first.gif",
]
for name in assets:
    with Image.open(ROOT / "assets" / name) as image:
        assert image.width == 1200 and image.height > 0
        if name.startswith("divider-"):
            assert image.height == 128 and image.n_frames == 1

measure = ImageDraw.Draw(Image.new("RGB", (1200, 128)))
assert measure.textlength("Clear interfaces. Resilient workflows. Responsible boundaries.", font=dividers.font("DejaVuSans.ttf", 25)) < 1144
assert hero.hero_frame().size == (1200, 420)
print("PASS: concise README, live portfolio links, seven target assets, readable headers, push ordering, branch names, empty/full feed layouts.")
