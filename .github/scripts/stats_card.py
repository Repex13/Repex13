"""Render a GitHub stats card from the account's own data.

Counts private contributions because it runs with the account token.
Uses the gh CLI, so it reads GH_TOKEN in Actions and the keyring locally.
"""
import json
import subprocess
import sys
from pathlib import Path

USER = "Repex13"
QUERY = """query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, first: 100) {
      nodes { stargazerCount isPrivate }
    }
    contributionsCollection {
      contributionCalendar { totalContributions }
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      totalRepositoriesWithContributedCommits
      restrictedContributionsCount
    }
  }
}"""

ICONS = {
    "star": "M12 2l2.9 6.3 6.9.7-5.2 4.6 1.5 6.8L12 16.9 5.9 20.4l1.5-6.8L2.2 9l6.9-.7z",
    "commit": "M12 7a5 5 0 100 10 5 5 0 000-10zm0 2a3 3 0 110 6 3 3 0 010-6zM11 1h2v4h-2zM11 19h2v4h-2zM1 11h4v2H1zM19 11h4v2h-4z",
    "pr": "M7 3a3 3 0 00-1 5.83v6.34a3 3 0 102 0V8.83A3 3 0 007 3zm10 11.17V9a3 3 0 00-3-3h-2l2-2-1-1.5L9.5 6 13 9.5l1-1.5-1.5-1.5H14a1 1 0 011 1v5.17a3 3 0 102 0z",
    "issue": "M12 2a10 10 0 100 20 10 10 0 000-20zm0 2a8 8 0 110 16 8 8 0 010-16zm0 4a1.5 1.5 0 100 3 1.5 1.5 0 000-3zm1 8h-2v-6h2z",
    "repo": "M4 3h11l5 5v13a1 1 0 01-1 1H4a1 1 0 01-1-1V4a1 1 0 011-1zm10 1.5V9h4.5z",
    "people": "M8 11a3.5 3.5 0 100-7 3.5 3.5 0 000 7zm8 0a3 3 0 100-6 3 3 0 000 6zM2 20c0-3.5 3-5.5 6-5.5s6 2 6 5.5v1H2zm14.5 1v-.7c0-2.4-1.8-4.3-4.2-5 2.7-.2 5.7 1.4 5.7 4.7v1z",
}


def fetch():
    out = subprocess.run(["gh", "api", "graphql", "-f", f"login={USER}", "-f", f"query={QUERY}"],
                         check=True, capture_output=True, text=True, encoding="utf-8").stdout
    u = json.loads(out)["data"]["user"]
    c = u["contributionsCollection"]
    stars = sum(r["stargazerCount"] for r in u["repositories"]["nodes"])
    return [("commit", "Total Contributions (last year)", c["contributionCalendar"]["totalContributions"]),
            ("star", "Total Stars", stars),
            ("pr", "Total PRs", c["totalPullRequestContributions"]),
            ("issue", "Total Issues", c["totalIssueContributions"]),
            ("repo", "Contributed to (last year)", c["totalRepositoriesWithContributedCommits"]),
            ("people", "Followers", u["followers"]["totalCount"])]


def render(stats):
    width, height = 495, 195
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
             'role="img" aria-label="GitHub stats">',
             "<style>.f{font-family:'Segoe UI',Ubuntu,'Helvetica Neue',Sans-Serif}"
             ".t{font-size:15px;font-weight:700;fill:#ffffff}.l{font-size:12.5px;fill:#d4d4d4}"
             ".n{font-size:12.5px;font-weight:700;fill:#ffffff}.i{opacity:0;animation:fade .45s ease-in-out forwards}"
             "@keyframes fade{to{opacity:1}}@media (prefers-reduced-motion:reduce){.i{opacity:1;animation:none}}</style>",
             f'<rect width="{width}" height="{height}" rx="10" fill="#000000"/>',
             '<text class="f t" x="25" y="34">GitHub Stats</text>']
    cols, col_w, row_h, y0 = 2, 235, 24, 66
    for i, (icon, label, num) in enumerate(stats):
        cx, cy = 25 + (i % cols) * col_w, y0 + (i // cols) * row_h
        parts.append(f'<g class="i" style="animation-delay:{i * 100}ms">'
                     f'<svg x="{cx}" y="{cy - 13}" width="15" height="15" viewBox="0 0 24 24">'
                     f'<path d="{ICONS[icon]}" fill="#bdbdbd"/></svg>'
                     f'<text class="f l" x="{cx + 21}" y="{cy}">{label}</text>'
                     f'<text class="f n" x="{cx + col_w - 10}" y="{cy}" text-anchor="end">{num:,}</text></g>')
    parts.append("</svg>")
    return "".join(parts)


def main(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stats = fetch()
    (out / "stats.svg").write_text(render(stats), encoding="utf-8")
    print(" | ".join(f"{label}={num}" for _, label, num in stats))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dist")
