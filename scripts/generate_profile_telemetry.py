"""Render the Signal GitHub contribution snapshot.

Run: python scripts/generate_profile_telemetry.py --user Jonnywik

Fetches the real GraphQL contribution window and renders both the compact
assets/github-activity-card.png card (blue/cyan Signal identity, self-hosted
Anton + Chakra Petch fonts) and the README contribution block betwen the
SNAPSHOT markers so scheduled refreshes keep the current wording.
"""
import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
FONTS = ASSETS / "fonts"
README = ROOT / "README.md"
WIDTH, HEIGHT = 1200, 460

# Signal palette (DESIGN.md / tokens.json)
NAVY = "#070E25"
PANEL = "#102344"
CARD = "#0C1B3A"
BORDER = "#34567F"
TEXT = "#F0F5FF"
MUTED = "#B8CCE8"
BLUE = "#95BAFF"
CYAN = "#88ECFF"
ACCENTS = [BLUE, CYAN, "#C2D6FA"]
START = "<!-- CONTRIBUTION_SNAPSHOT:START -->"
END = "<!-- CONTRIBUTION_SNAPSHOT:END -->"

QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) { totalCount }
    contributionsCollection {
      startedAt
      endedAt
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def load_font(filename, size):
    candidate = FONTS / filename
    if candidate.exists():
        return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default(size=size)


def strip_ansi(value):
    return re.sub(r"\x1B\[[0-9;]*[A-Za-z]", "", value)


def run_query(user):
    variables = json.dumps({"login": user})
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        response = requests.post(
            "https://api.github.com/graphql",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            json={"query": QUERY, "variables": {"login": user}},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
    else:
        result = subprocess.run(
            ["gh", "api", "graphql", "-f", f"query={QUERY}", "-F", f"login={user}"],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(strip_ansi(result.stdout))
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]["user"]


def pretty_date(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    return f"{parsed.strftime('%b')} {parsed.day}, {parsed.year}"


def metrics(user):
    collection = user["contributionsCollection"]
    calendar = collection["contributionCalendar"]
    return {
        "calendar": calendar["totalContributions"],
        "commits": collection["totalCommitContributions"],
        "repos": user["repositories"]["totalCount"],
        "window": f"{pretty_date(collection['startedAt'])} – {pretty_date(collection['endedAt'])}",
    }


def render(data):
    output = ASSETS / "github-activity-card.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    heading = load_font("anton-400.ttf", 40)
    value = load_font("anton-400.ttf", 62)
    label = load_font("chakrapetch-500.ttf", 19)
    small = load_font("chakrapetch-400.ttf", 18)
    image = Image.new("RGB", (WIDTH, HEIGHT), NAVY)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2, 2, WIDTH - 3, HEIGHT - 3), radius=22, fill=CARD, outline=BORDER, width=2)
    draw.rectangle((48, 40, 54, 92), fill=CYAN)
    draw.text((76, 38), "Contribution snapshot", font=heading, fill=TEXT)
    draw.text((78, 92), "Real GitHub GraphQL totals · dated snapshot", font=small, fill=MUTED)
    stats = [
        ("Calendar contributions", data["calendar"]),
        ("Commit contributions", data["commits"]),
        ("Public owned repositories", data["repos"]),
    ]
    column = (WIDTH - 64) // 3
    for index, (title, count) in enumerate(stats):
        x = 32 + index * column
        accent = ACCENTS[index % len(ACCENTS)]
        draw.line((x + 16, 160, x + column - 32, 160), fill=accent, width=4)
        draw.text((x + 16, 182), str(count), font=value, fill=TEXT)
        draw.text((x + 18, 262), title, font=label, fill=MUTED)
    draw.line((48, 330, WIDTH - 48, 330), fill=BORDER, width=1)
    draw.text((48, 352), "GraphQL window", font=small, fill=CYAN)
    draw.text((48, 380), data["window"], font=load_font("chakrapetch-500.ttf", 24), fill=TEXT)
    draw.text((48, 418), "GitHub-reported contribution totals · repository count is public only.", font=small, fill=MUTED)
    image.save(output, "PNG", optimize=True)
    return output


def markdown_block(data):
    return "\n".join(
        [
            START,
            "",
            "| Calendar contributions | Commit contributions | Public owned repositories |",
            "| --- | --- | --- |",
            f"| {data['calendar']} | {data['commits']} | {data['repos']} |",
            "",
            f"Real GitHub GraphQL snapshot · window {data['window']} · refreshed automatically.",
            "",
            END,
        ]
    )


def update_readme(block):
    readme = README.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        raise RuntimeError("README contribution markers are missing.")
    updated = re.sub(f"{re.escape(START)}.*?{re.escape(END)}", block, readme, flags=re.DOTALL)
    README.write_text(updated, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Render the Signal GitHub contribution snapshot.")
    parser.add_argument("--user", default="Jonnywik", help="Public GitHub login to render.")
    parser.add_argument("--no-readme", action="store_true", help="Only render the card image.")
    args = parser.parse_args()
    data = metrics(run_query(args.user))
    print(render(data))
    if not args.no_readme:
        update_readme(markdown_block(data))
        print(README)


if __name__ == "__main__":
    main()
