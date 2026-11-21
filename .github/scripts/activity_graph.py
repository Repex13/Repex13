"""Render a contribution activity graph from the account's own calendar.

Counts private contributions because it runs with the account token.
Uses the gh CLI, so it reads GH_TOKEN in Actions and the keyring locally.
"""
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

USER = "Repex13"
DAYS = 42
QUERY = """query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}"""


def fetch():
    out = subprocess.run(["gh", "api", "graphql", "-f", f"login={USER}", "-f", f"query={QUERY}"],
                         check=True, capture_output=True, text=True, encoding="utf-8").stdout
    cal = json.loads(out)["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [(d["date"], d["contributionCount"])
            for w in cal["weeks"] for d in w["contributionDays"]]
    return cal["totalContributions"], sorted(days)


def render(total, days):
    width, height = 990, 260
    left, right, top, bottom = 42, 20, 46, 40
    plot_w, plot_h = width - left - right, height - top - bottom
    counts = [c for _, c in days]
    peak = max(counts) or 1
    step = plot_w / (len(days) - 1)
    pts = [(left + i * step, top + plot_h * (1 - c / peak)) for i, c in enumerate(counts)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{left:.1f},{top + plot_h} " + line + f" {left + (len(days) - 1) * step:.1f},{top + plot_h}"
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
             'role="img" aria-label="Contribution activity graph">',
             "<style>.f{font-family:'Segoe UI',Ubuntu,'Helvetica Neue',Sans-Serif}"
             ".t{font-size:16px;font-weight:700;fill:#ffffff}.a{font-size:11px;fill:#8a8a8a}"
             ".i{opacity:0;animation:fade .6s ease-in-out forwards}@keyframes fade{to{opacity:1}}"
             "@media (prefers-reduced-motion:reduce){.i{opacity:1;animation:none}}</style>",
             f'<rect width="{width}" height="{height}" rx="10" fill="#000000"/>',
             f'<text class="f t" x="{left}" y="30">Contribution Graph</text>',
             f'<text class="f a" x="{width - right}" y="30" text-anchor="end">'
             f'{total:,} contributions in the last year</text>',
             '<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
             '<stop offset="0" stop-color="#ffffff" stop-opacity=".28"/>'
             '<stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient></defs>']
    for i in range(5):
        gy = top + plot_h * i / 4
        val = round(peak * (4 - i) / 4)
        parts.append(f'<line x1="{left}" y1="{gy:.1f}" x2="{width - right}" y2="{gy:.1f}" stroke="#222222"/>'
                     f'<text class="f a" x="{left - 7}" y="{gy + 4:.1f}" text-anchor="end">{val}</text>')
    first, last = date.fromisoformat(days[0][0]), date.fromisoformat(days[-1][0])
    n_labels = 6
    for i in range(n_labels):
        d = first + (last - first) * i / (n_labels - 1)
        x = left + plot_w * i / (n_labels - 1)
        parts.append(f'<text class="f a" x="{x:.0f}" y="{height - 14}" text-anchor="middle">'
                     f'{d.strftime("%b")} {d.day}</text>')
    parts.append(f'<g class="i"><polygon points="{area}" fill="url(#g)"/>'
                 f'<polyline points="{line}" fill="none" stroke="#ffffff" stroke-width="2"/>')
    hi = counts.index(peak)
    parts.append(f'<circle cx="{pts[hi][0]:.1f}" cy="{pts[hi][1]:.1f}" r="4" fill="#ffffff"/>'
                 f'<text class="f a" x="{min(pts[hi][0] + 8, width - right - 30):.0f}" y="{pts[hi][1] - 6:.1f}">{peak}</text>')
    parts.append("</g></svg>")
    return "".join(parts)


def main(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    total, days = fetch()
    cutoff = (date.today() - timedelta(days=DAYS - 1)).isoformat()
    days = [d for d in days if d[0] >= cutoff]
    (out / "activity-graph.svg").write_text(render(total, days), encoding="utf-8")
    print(f"total={total} window={days[0][0]}..{days[-1][0]} peak={max(c for _, c in days)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dist")
