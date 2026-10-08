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
WIDTH, HEIGHT = 1200, 460
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
    windows_font = "segoeuib.ttf" if "Bold" in filename else "segoeui.ttf"
    for path in [f"/usr/share/fonts/truetype/dejavu/{filename}", f"C:/Windows/Fonts/{windows_font}"]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


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
    for event in sorted(events, key=lambda event: event["created_at"], reverse=True):
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
                "branch": event.get("payload", {}).get("ref", "refs/heads/main").removeprefix("refs/heads/"),
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
    return sorted([node for node in nodes if node.get("pullRequestReview")], key=lambda node: node["occurredAt"], reverse=True)


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
    heading = load_font("DejaVuSans-Bold.ttf", 40)
    body = load_font("DejaVuSans.ttf", 28)
    small = load_font("DejaVuSans.ttf", 24)
    separator_y = 140 + 53 * max(1, len(pushes))
    height = separator_y + 108
    image = Image.new("RGB", (WIDTH, height), INK)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2, 2, WIDTH - 3, height - 3), radius=16, fill=PANEL, outline=LINE, width=2)
    draw.text((32, 24), "Recent public activity", font=heading, fill=TEXT)
    draw.text((32, 82), "Latest push per repository · GitHub's event feed may lag", font=small, fill=MUTED)
    if not pushes:
        draw.text((32, 140), "No public pushes found in the event feed.", font=body, fill=MUTED)
    for index, entry in enumerate(pushes):
        y = 128 + index * 53
        draw.rectangle((32, y + 5, 36, y + 37), fill=ACCENTS[index % len(ACCENTS)])
        repo_label = entry["repo"]
        while draw.textlength(repo_label, font=body) > 650:
            repo_label = repo_label[:-2] + "…"
        draw.text((52, y), repo_label, font=body, fill=TEXT)
        draw.text((746, y + 3), entry["sha"], font=small, fill=TEAL)
        draw.text((940, y + 3), entry["time"].strftime("%Y-%m-%d"), font=small, fill=MUTED)
    draw.line((32, separator_y, 1168, separator_y), fill=LINE, width=2)
    if reviews:
        review = reviews[0]["pullRequestReview"]
        copy = "Latest PR review: " + review["state"].replace("_", " ").lower()
    else:
        copy = "PR reviews: none recorded in GitHub's contribution window."
    draw.text((32, separator_y + 15), copy, font=small, fill=MUTED)
    draw.text((32, separator_y + 65), f"Updated {datetime.now(timezone.utc).date().isoformat()} UTC · GitHub public events", font=small, fill=MUTED)
    image.save(output, "PNG", optimize=True)
    return output


def markdown_block(pushes, reviews):
    lines = [START, ""]
    if not pushes:
        lines.extend(["No public pushes found in GitHub's current event feed.", ""])
    for entry in pushes:
        lines.append(
            f"- [{entry['repo']} · `{entry['sha']}`]({entry['url']}) — pushed to `{entry['branch']}` on {entry['time'].strftime('%Y-%m-%d')} UTC."
        )
        lines.append("")
    if reviews:
        for review_node in reviews[:2]:
            review = review_node["pullRequestReview"]
            pull_request = review["pullRequest"]
            lines.append(
                f"- [PR review · {pull_request['repository']['nameWithOwner']}]({review['url']}) — {review['state'].replace('_', ' ').lower()} on {parse_time(review_node['occurredAt']).strftime('%Y-%m-%d')} UTC."
            )
            lines.append("")
    else:
        lines.extend(["No public PR reviews recorded in GitHub's contribution window.", ""])
    lines.append(END)
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
