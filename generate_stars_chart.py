"""
Generates a "cumulative stars over time" chart for a chosen list of repos,
using GitHub's stargazers API (with starred_at timestamps).

Usage:
    python generate_stars_chart.py

Requires:
    pip install requests matplotlib

Environment variable:
    GITHUB_TOKEN - a GitHub token with public_repo (read) scope.
                   In GitHub Actions this is provided automatically as
                   secrets.GITHUB_TOKEN.
"""

import os
import sys
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import requests

# --- Configure your repos here (owner/repo) ---
REPOS = [
    "AneeshkrMoury/CoachBot",
    # add more "owner/repo" strings as you like
]

GITHUB_API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN")

HEADERS = {
    "Accept": "application/vnd.github.star+json",  # needed to get starred_at
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def fetch_star_timestamps(repo: str) -> list[datetime]:
    """Fetch all starred_at timestamps for a repo (paginated)."""
    timestamps = []
    page = 1
    while True:
        url = f"{GITHUB_API}/repos/{repo}/stargazers"
        resp = requests.get(
            url, headers=HEADERS, params={"per_page": 100, "page": page}
        )
        if resp.status_code == 404:
            print(f"WARNING: repo not found or private: {repo}", file=sys.stderr)
            return []
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        for entry in data:
            ts = entry.get("starred_at")
            if ts:
                timestamps.append(
                    datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
                )
        page += 1
    return sorted(timestamps)


def main():
    if not REPOS:
        print("No repos configured in REPOS list.", file=sys.stderr)
        sys.exit(1)

    plt.figure(figsize=(10, 6))

    any_data = False
    for repo in REPOS:
        timestamps = fetch_star_timestamps(repo)
        if not timestamps:
            continue
        any_data = True
        cumulative = list(range(1, len(timestamps) + 1))
        plt.plot(timestamps, cumulative, label=repo, linewidth=2)

    if not any_data:
        print("No star data retrieved for any repo — check REPOS list / token.", file=sys.stderr)
        sys.exit(1)

    plt.title("Total number of stars over time")
    plt.xlabel("Year")
    plt.ylabel("Cumulative number of stars")
    plt.legend(loc="upper left", fontsize=8)
    plt.gca().xaxis.set_major_locator(mdates.YearLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    plt.grid(alpha=0.3)
    plt.tight_layout()

    os.makedirs("assets", exist_ok=True)
    out_path = "assets/stars_over_time.png"
    plt.savefig(out_path, dpi=150)
    print(f"Saved chart to {out_path}")


if __name__ == "__main__":
    main()
