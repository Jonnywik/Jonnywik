import argparse
import json
import os
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 1200, 286
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
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{filename}", size)


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


def draw_metric(draw, x, label, value, accent, mono, display):
    draw.rounded_rectangle((x, 187, x + 127, 247), radius=6, fill="#0b1117", outline=LINE, width=1)
    draw.rectangle((x, 187, x + 4, 247), fill=accent)
    draw.text((x + 16, 198), label, font=mono, fill=MUTED)
    draw.text((x + 16, 213), str(value), font=display, fill=TEXT)


def render(user, payload):
    root = Path(__file__).resolve().parents[1]
    output = root / "assets" / "github-activity-card.png"
    output.parent.mkdir(parents=True, exist_ok=True)

    display = load_font("DejaVuSans-Bold.ttf", 26)
    heading = load_font("DejaVuSans-Bold.ttf", 21)
    mono = load_font("DejaVuSansMono.ttf", 10)
    mono_small = load_font("DejaVuSansMono.ttf", 9)

    calendar = payload["contributionsCollection"]["contributionCalendar"]
    weeks = calendar["weeks"]
    languages = Counter(
        node["primaryLanguage"]["name"]
        for node in payload["repositories"]["nodes"]
        if node["primaryLanguage"]
    )
    top_languages = " / ".join(language.upper() for language, _ in languages.most_common(3)) or "PUBLIC SOURCE"
    pinned = payload.get("pinnedItems", {}).get("totalCount", 0)
    metrics = [
        ("PUBLIC REPOS", payload["repositories"]["totalCount"], TEAL),
        (f"{date.today().year} SIGNALS", calendar["totalContributions"], AMBER),
        ("PINNED SYSTEMS", pinned, VIOLET),
        ("FOLLOWERS", payload["followers"]["totalCount"], MINT),
    ]

    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    for x in range(0, WIDTH, 48):
        draw.line((x, 0, x, HEIGHT), fill="#121d25", width=1)
    for y in range(0, HEIGHT, 48):
        draw.line((0, y, WIDTH, y), fill="#121d25", width=1)
    draw.rounded_rectangle((20, 18, WIDTH - 20, HEIGHT - 18), radius=10, outline=LINE, width=1, fill=PANEL)

    draw.rectangle((46, 42, 50, 144), fill=TEAL)
    draw.text((66, 42), "GITHUB / CONTRIBUTION TELEMETRY", font=mono, fill=TEAL)
    draw.text((66, 66), "Contribution field", font=heading, fill=TEXT)
    draw.text((66, 96), f"{date.today().year} / PUBLIC ACTIVITY SNAPSHOT", font=mono_small, fill=MUTED)
    draw.text((66, 116), "DAILY SELF-HOSTED REFRESH", font=mono_small, fill=VIOLET)
    draw.text((66, 137), top_languages, font=mono_small, fill=MINT)

    field_x, field_y, cell, gap = 366, 67, 10, 4
    draw.text((field_x, 38), f"CONTRIBUTION DENSITY / {date.today().year}", font=mono, fill=TEAL)
    month_positions = set()
    for week_index, week in enumerate(weeks):
        for day in week["contributionDays"]:
            parsed = date.fromisoformat(day["date"])
            if parsed.day <= 7 and parsed.month not in month_positions:
                month_positions.add(parsed.month)
                draw.text((field_x + week_index * (cell + gap), 50), parsed.strftime("%b").upper(), font=mono_small, fill=MUTED)
            weekday = parsed.weekday()
            x = field_x + week_index * (cell + gap)
            y = field_y + weekday * (cell + gap)
            color = contribution_level(day["contributionCount"])
            draw.rounded_rectangle((x, y, x + cell, y + cell), radius=2, fill=color)

    draw.text((field_x, 166), "LOW", font=mono_small, fill=MUTED)
    for index, color in enumerate([EMPTY, "#1d5956", TEAL, MINT, AMBER]):
        x = field_x + 31 + index * 18
        draw.rounded_rectangle((x, 164, x + 12, 176), radius=2, fill=color)
    draw.text((field_x + 132, 166), "HIGH", font=mono_small, fill=MUTED)
    draw.text((field_x + 208, 166), "AMBER = HIGH-ACTIVITY SIGNAL", font=mono_small, fill=AMBER)

    for index, metric in enumerate(metrics):
        draw_metric(draw, 366 + index * 151, *metric, mono, display)

    draw.text((46, 258), f"REFRESHED / {date.today().isoformat()}  ·  SOURCE / GITHUB PUBLIC GRAPHQL DATA", font=mono_small, fill=MUTED)
    draw.text((910, 258), f"{user.upper()} / COMMAND CENTER", font=mono_small, fill=TEAL)
    image.save(output, "PNG", optimize=True)
    print(output)


def main():
    parser = argparse.ArgumentParser(description="Render a self-hosted GitHub contribution telemetry chart.")
    parser.add_argument("--user", default="Jonnywik", help="Public GitHub login to render.")
    args = parser.parse_args()
    current_year = date.today().year
    query = f'''
    query {{
      user(login: "{args.user}") {{
        followers {{ totalCount }}
        pinnedItems(first: 6) {{ totalCount }}
        repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) {{
          totalCount
          nodes {{ primaryLanguage {{ name }} }}
        }}
        contributionsCollection(from: "{current_year}-01-01T00:00:00Z", to: "{current_year}-12-31T23:59:59Z") {{
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
