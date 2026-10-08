import argparse
import json
import os
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 1200, 460
BACKGROUND = "#090d12"
PANEL = "#101820"
LINE = "#263440"
MUTED = "#8d9ca8"
TEXT = "#dce8ed"
TEAL = "#2dd4bf"
MINT = "#a7f3d0"
AMBER = "#fbbf24"
VIOLET = "#a78bfa"
EMPTY = "#18252e"


def load_font(filename: str, size: int):
    windows_font = "segoeuib.ttf" if "Bold" in filename else "segoeui.ttf"
    for path in [f"/usr/share/fonts/truetype/dejavu/{filename}", f"C:/Windows/Fonts/{windows_font}"]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def run_query(query: str):
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        response = requests.post(
            "https://api.github.com/graphql",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            json={"query": query},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
    else:
        command = ["gh", "api", "graphql", "-F", f"query={query}"]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]["user"]


def contribution_level(count: int):
    if count == 0:
        return EMPTY
    if count == 1:
        return "#1d5956"
    if count <= 3:
        return TEAL
    if count <= 6:
        return MINT
    return AMBER


def render(user, payload):
    root = Path(__file__).resolve().parents[1]
    output = root / "assets" / "github-activity-card.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    heading = load_font("DejaVuSans-Bold.ttf", 40)
    label = load_font("DejaVuSans.ttf", 24)
    value = load_font("DejaVuSans-Bold.ttf", 46)
    small = load_font("DejaVuSans.ttf", 21)
    calendar = payload["contributionsCollection"]["contributionCalendar"]
    weeks = calendar["weeks"]
    year = datetime.now(timezone.utc).year
    metrics = [
        ("Public repositories", payload["repositories"]["totalCount"], TEAL),
        (f"Contributions in {year}", calendar["totalContributions"], AMBER),
        ("Pinned projects", payload.get("pinnedItems", {}).get("totalCount", 0), VIOLET),
        ("Followers", payload["followers"]["totalCount"], MINT),
    ]
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2, 2, WIDTH - 3, HEIGHT - 3), radius=16, fill=PANEL, outline=LINE, width=2)
    draw.text((32, 24), "GitHub contribution stats", font=heading, fill=TEXT)
    for index, (title, count, accent) in enumerate(metrics):
        x = 32 + index * 292
        draw.line((x, 106, x + 264, 106), fill=accent, width=3)
        draw.text((x, 124), str(count), font=value, fill=TEXT)
        draw.text((x, 182), title, font=label, fill=MUTED)
    # Match GitHub's Sunday-first calendar and only show returned days.
    field_x, field_y, cell, gap = 32, 265, 13, 6
    months = set()
    for week_index, week in enumerate(weeks):
        for day in week["contributionDays"]:
            parsed = date.fromisoformat(day["date"])
            if parsed.day <= 7 and parsed.month not in months:
                months.add(parsed.month)
                draw.text((field_x + week_index * (cell + gap), 230), parsed.strftime("%b"), font=small, fill=MUTED)
            x = field_x + week_index * (cell + gap)
            y = field_y + ((parsed.weekday() + 1) % 7) * (cell + gap)
            draw.rounded_rectangle((x, y, x + cell, y + cell), radius=2, fill=contribution_level(day["contributionCount"]))
    draw.text((32, 420), f"Updated {datetime.now(timezone.utc).date().isoformat()} UTC · GitHub contribution data", font=small, fill=MUTED)
    draw.text((1048, 258), "Less", font=small, fill=MUTED)
    for index, color in enumerate([EMPTY, "#1d5956", TEAL, MINT, AMBER]):
        y = 292 + index * 19
        draw.rounded_rectangle((1050, y, 1063, y + 13), radius=2, fill=color)
    draw.text((1080, 362), "More", font=small, fill=MUTED)
    image.save(output, "PNG", optimize=True)
    print(output)


def main():
    parser = argparse.ArgumentParser(description="Render a self-hosted GitHub contribution telemetry chart.")
    parser.add_argument("--user", default="Jonnywik", help="Public GitHub login to render.")
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    current_year = now.year
    end_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    query = f'''
    query {{
      user(login: "{args.user}") {{
        followers {{ totalCount }}
        pinnedItems(first: 6) {{ totalCount }}
        repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) {{
          totalCount
          nodes {{ primaryLanguage {{ name }} }}
        }}
        contributionsCollection(from: "{current_year}-01-01T00:00:00Z", to: "{end_time}") {{
          contributionCalendar {{
            totalContributions
            weeks {{ contributionDays {{ date contributionCount }} }}
          }}
        }}
      }}
    }}
    '''
    render(args.user, run_query(query))


if __name__ == "__main__":
    main()
