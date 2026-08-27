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
README = ROOT / "README.md"
WIDTH, HEIGHT = 1200, 250
INK = "#090d12"
PANEL = "#101820"
LINE = "#263440"
TEXT = "#dce8ed"
MUTED = "#8d9ca8"
TEAL = "#2dd4bf"
MINT = "#a7f3d0"
AMBER = "#fbbf24"
VIOLET = "#a78bfa"
ACCENTS = [TEAL, MINT, AMBER, VIOLET]
START = "<!-- RECENT_ACTIVITY:START -->"
END = "<!-- RECENT_ACTIVITY:END -->"


def load_font(filename: str, size: int):
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{filename}", size)


def strip_ansi(value: str):
    return re.sub(r"\x1B\[[0-9;]*[A-Za-z]", "", value)


def github_json(path: str):
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        response = requests.get(
            f"https://api.github.com/{path}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    result = subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True)
    return json.loads(strip_ansi(result.stdout))


def graphql_json(query: str):
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
        result = subprocess.run(["gh", "api", "graphql", "-F", f"query={query}"], check=True, capture_output=True, text=True)
        payload = json.loads(strip_ansi(result.stdout))
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]


def parse_time(value: str):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def recent_pushes(user: str):
    events = github_json(f"users/{user}/events/public?per_page=100")
    entries, seen_repositories = [], set()
    for event in events:
        if event.get("type") != "PushEvent":
            continue
        repo = event["repo"]["name"]
        head = event.get("payload", {}).get("head")
        if not head or repo in seen_repositories:
            continue
        seen_repositories.add(repo)
        entries.append(
            {
                "repo": repo,
                "branch": event.get("payload", {}).get("ref", "refs/heads/main").split("/")[-1],
                "sha": head[:7],
                "url": f"https://github.com/{repo}/commit/{head}",
                "time": parse_time(event["created_at"]),
            }
        )
        if len(entries) == 4:
            break
    return entries


def recent_reviews(user: str):
    query = f'''
    query {{
      user(login: "{user}") {{
        contributionsCollection {{
          pullRequestReviewContributions(first: 3) {{
            nodes {{
              occurredAt
              pullRequestReview {{
                state
                url
                pullRequest {{
                  title
                  repository {{ nameWithOwner }}
                }}
              }}
            }}
          }}
        }}
      }}
    }}
    '''
    nodes = graphql_json(query)["user"]["contributionsCollection"]["pullRequestReviewContributions"]["nodes"]
    return [node for node in nodes if node.get("pullRequestReview")]


def relative_time(moment: datetime):
    seconds = max(0, int((datetime.now(timezone.utc) - moment).total_seconds()))
    if seconds < 3600:
        return f"{max(1, seconds // 60)}M AGO"
    if seconds < 86400:
        return f"{seconds // 3600}H AGO"
    return f"{seconds // 86400}D AGO"


def short_repo(repo: str):
    return repo.split("/", 1)[-1].upper().replace("-", " ")[:23]


def render(pushes, reviews):
    output = ASSETS / "recent-activity-feed.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    display = load_font("DejaVuSans-Bold.ttf", 17)
    mono = load_font("DejaVuSansMono.ttf", 10)
    mono_small = load_font("DejaVuSansMono.ttf", 9)
    image = Image.new("RGB", (WIDTH, HEIGHT), INK)
    draw = ImageDraw.Draw(image)
    for x in range(0, WIDTH, 48):
        draw.line((x, 0, x, HEIGHT), fill="#121d25", width=1)
    for y in range(0, HEIGHT, 48):
        draw.line((0, y, WIDTH, y), fill="#121d25", width=1)
    draw.rounded_rectangle((20, 18, WIDTH - 20, HEIGHT - 18), radius=10, outline=LINE, width=1, fill=PANEL)
    draw.rectangle((46, 40, 50, 208), fill=VIOLET)
    draw.text((66, 40), "GITHUB / RECENT ACTIVITY", font=mono, fill=VIOLET)
    draw.text((66, 63), "Commit signal feed", font=display, fill=TEXT)
    draw.text((66, 89), "LATEST PUBLIC PUSHES ACROSS REPOSITORIES", font=mono_small, fill=MUTED)

    row_y = 116
    for index, entry in enumerate(pushes):
        accent = ACCENTS[index % len(ACCENTS)]
        draw.rounded_rectangle((66, row_y, 820, row_y + 23), radius=4, fill="#0b1117", outline=LINE, width=1)
        draw.rectangle((66, row_y, 70, row_y + 23), fill=accent)
        draw.text((82, row_y + 7), f"PUSH / {short_repo(entry['repo'])} / {entry['branch'].upper()}", font=mono_small, fill=TEXT)
        draw.text((534, row_y + 7), entry["sha"], font=mono_small, fill=accent)
        draw.text((675, row_y + 7), relative_time(entry["time"]), font=mono_small, fill=MUTED)
        row_y += 27

    draw.rounded_rectangle((858, 40, 1124, 208), radius=8, fill="#0b1117", outline=LINE, width=1)
    draw.text((883, 61), "PR REVIEW SIGNAL", font=mono, fill=AMBER)
    if reviews:
        review = reviews[0]["pullRequestReview"]
        draw.text((883, 90), review["state"].upper(), font=display, fill=MINT)
        draw.text((883, 118), short_repo(review["pullRequest"]["repository"]["nameWithOwner"]), font=mono_small, fill=TEXT)
        draw.text((883, 139), "PUBLIC REVIEW ACTIVITY", font=mono_small, fill=MUTED)
        draw.text((883, 166), relative_time(parse_time(reviews[0]["occurredAt"])), font=mono, fill=AMBER)
    else:
        draw.text((883, 89), "NO REVIEW SIGNAL", font=display, fill=TEXT)
        draw.text((883, 118), "No public PR review", font=mono_small, fill=MUTED)
        draw.text((883, 134), "contributions recorded", font=mono_small, fill=MUTED)
        draw.text((883, 169), "STATUS / STANDBY", font=mono, fill=AMBER)
    draw.text((66, 223), f"REFRESHED / {datetime.now(timezone.utc).date().isoformat()} UTC  ·  SOURCE / GITHUB PUBLIC EVENTS + GRAPHQL", font=mono_small, fill=MUTED)
    draw.text((946, 223), "OPEN COMMIT ROUTES", font=mono_small, fill=TEAL)
    image.save(output, "PNG", optimize=True)
    return output


def markdown_block(pushes, reviews):
    lines = [START, "<details>", "<summary><strong>OPEN RECENT SIGNALS</strong><br />Latest public pushes and PR review state</summary>", ""]
    for entry in pushes:
        lines.append(
            f"**[{entry['repo']} · {entry['sha']}]({entry['url']})**: pushed to `{entry['branch']}` {relative_time(entry['time']).lower()}."
        )
        lines.append("")
    if reviews:
        for review_node in reviews[:2]:
            review = review_node["pullRequestReview"]
            pull_request = review["pullRequest"]
            lines.append(
                f"**[PR review · {pull_request['repository']['nameWithOwner']}]({review['url']})**: `{review['state'].lower()}` {relative_time(parse_time(review_node['occurredAt'])).lower()}."
            )
            lines.append("")
    else:
        lines.extend(["**PR review signal:** No public review contributions are recorded in the current activity window.", ""])
    lines.extend(["**[View live GitHub activity](https://github.com/Jonnywik)** · **[Open repositories](https://github.com/Jonnywik?tab=repositories)**", "", "</details>", END])
    return "\n".join(lines)


def update_readme(block: str):
    readme = README.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        raise RuntimeError("README activity-feed markers are missing.")
    updated = re.sub(f"{re.escape(START)}.*?{re.escape(END)}", block, readme, flags=re.DOTALL)
    README.write_text(updated, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Render a self-hosted GitHub recent-activity feed.")
    parser.add_argument("--user", default="Jonnywik", help="Public GitHub login to render.")
    args = parser.parse_args()
    pushes = recent_pushes(args.user)
    reviews = recent_reviews(args.user)
    output = render(pushes, reviews)
    update_readme(markdown_block(pushes, reviews))
    print(output)


if __name__ == "__main__":
    main()
