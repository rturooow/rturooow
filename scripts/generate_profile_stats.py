from datetime import datetime, timezone
from json import load
from os import environ
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape


API_URL = "https://api.github.com"
API_VERSION = "2026-03-10"
USERNAME = environ.get("GITHUB_USERNAME", "rturooow")
TOKEN = environ.get("GITHUB_TOKEN")


def fetch_json(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "rturooow-profile-stats",
        "X-GitHub-Api-Version": API_VERSION,
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    request = Request(url, headers=headers)
    with urlopen(request, timeout=30) as response:
        return load(response)


def collect_stats():
    profile = fetch_json(f"{API_URL}/users/{USERNAME}")
    stars = 0
    page = 1

    while True:
        repos = fetch_json(
            f"{API_URL}/users/{USERNAME}/repos?type=owner&per_page=100&page={page}"
        )
        stars += sum(int(repo.get("stargazers_count", 0)) for repo in repos)
        if len(repos) < 100:
            break
        page += 1

    return {
        "repositories": int(profile["public_repos"]),
        "stars": stars,
        "followers": int(profile["followers"]),
    }


def make_svg(stats):
    updated = datetime.now(timezone.utc).strftime("%b %d, %Y").upper()
    columns = (
        (70, "PUBLIC REPOSITORIES", stats["repositories"]),
        (410, "STARS ON MY REPOSITORIES", stats["stars"]),
        (750, "FOLLOWERS", stats["followers"]),
    )
    fields = []
    for x, label, value in columns:
        fields.append(
            f'  <text x="{x}" y="57" fill="#aab6ac" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="12" letter-spacing="1">{label}</text>\n'
            f'  <text x="{x}" y="111" fill="#f1f4ef" font-family="Inter, Segoe UI, Arial, sans-serif" font-size="38" font-weight="600">{value:,}</text>'
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="164" viewBox="0 0 1000 164" role="img" aria-labelledby="title description">
  <title id="title">GitHub profile stats for {escape(USERNAME)}</title>
  <desc id="description">{stats["repositories"]} public repositories, {stats["stars"]} stars across owned repositories, and {stats["followers"]} followers. Updated {updated} UTC.</desc>
  <rect x="0.5" y="0.5" width="999" height="163" rx="12" fill="#0d120f" stroke="#26352b" />
  <path d="M354 32V126M694 32V126" stroke="#26352b" />
{chr(10).join(fields)}
  <text x="930" y="145" text-anchor="end" fill="#819087" font-family="Inter, 'Segoe UI', Arial, sans-serif" font-size="10" letter-spacing="0.8">UPDATED {updated} UTC</text>
</svg>
'''


def main():
    try:
        stats = collect_stats()
    except HTTPError as error:
        raise SystemExit(f"GitHub API request failed: HTTP {error.code}") from error

    output_path = Path(__file__).resolve().parents[1] / "profile" / "stats.svg"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(make_svg(stats), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
