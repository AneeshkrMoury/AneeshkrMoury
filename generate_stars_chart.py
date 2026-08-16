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
    "AneeshkrMoury/Python_Learning_And_Practive",
    "AneeshkrMoury/unidep",
    "AneeshkrMoury/truthlens",
    "AneeshkrMoury/AneeshkrMoury.github.io",
    "AneeshkrMoury/StressPPG",
    "AneeshkrMoury/first-contributions",
    "AneeshkrMoury/UtilityApp",
    "AneeshkrMoury/today-in-history",
    "AneeshkrMoury/Learn2Trade",
]

GITHUB_API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN")

HEADERS = {
    "Accept": "application/vnd.github.star+json",  # needed to get starred_at
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def fetch_star_timestamps(repo: str) -> list[datetime]:
    """Fetch all starred_at timestamps for a repo (paginated).
    Never raises — returns [] and prints a warning on any problem
    (private repo, not found, rate-limited, network error, etc.)."""
    timestamps = []
    page = 1
    try:
        while True:
            url = f"{GITHUB_API}/repos/{repo}/stargazers"
            resp = requests.get(
                url, headers=HEADERS, params={"per_page": 100, "page": page}, timeout=15
            )
            if resp.status_code == 404:
                print(f"SKIP: repo not found or private: {repo}", file=sys.stderr)
                return []
            if resp.status_code == 403:
                print(f"SKIP: rate-limited or forbidden fetching {repo}: {resp.text[:200]}", file=sys.stderr)
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
    except Exception as e:
        print(f"SKIP: error fetching {repo}: {e}", file=sys.stderr)
        return []
    return sorted(timestamps)


def main():
    os.makedirs("assets", exist_ok=True)
    out_path = "assets/stars_over_time.png"

    if not REPOS:
        print("No repos configured in REPOS list — writing placeholder chart.", file=sys.stderr)
        REPOS.clear()

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
        # No usable star data yet (repos are private, new, or have 0 stars).
        # Still produce a valid placeholder chart instead of failing the workflow,
        # so the README image link never breaks.
        print("No star data available yet — saving placeholder chart.", file=sys.stderr)
        plt.text(
            0.5, 0.5,
            "No public star data yet — check back later!",
            ha="center", va="center", fontsize=12, transform=plt.gca().transAxes,
        )
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(out_path, dpi=150)
        print(f"Saved placeholder chart to {out_path}")
        return

    plt.title("Total number of stars over time")
    plt.xlabel("Year")
    plt.ylabel("Cumulative number of stars")
    plt.legend(loc="upper left", fontsize=8)
    plt.gca().xaxis.set_major_locator(mdates.YearLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    print(f"Saved chart to {out_path}")


if __name__ == "__main__":
    main()
