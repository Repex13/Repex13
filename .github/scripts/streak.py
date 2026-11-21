"""Render a contribution-streak card from the user's own contribution calendar.

Counts private contributions because it runs with the account token.
Uses the gh CLI, so it reads GH_TOKEN in Actions and the keyring locally.
"""
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

USER = "Repex13"
QUERY = """query($login: String!) {
  user(login: $login) {
    contributionsCollection%s {
      contributionYears
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}"""


def calendar(range_args=""):
    out = subprocess.run(["gh", "api", "graphql", "-f", f"login={USER}",
                          "-f", f"query={QUERY % range_args}"],
                         check=True, capture_output=True, text=True, encoding="utf-8").stdout
    coll = json.loads(out)["data"]["user"]["contributionsCollection"]
    cal = coll["contributionCalendar"]
    days = [(d["date"], d["contributionCount"])
            for w in cal["weeks"] for d in w["contributionDays"]]
    return cal["totalContributions"], days, coll.get("contributionYears") or []


def first_contribution(years):
    if not years:
        return None
    first_year = min(years)
    _, days, _ = calendar(
        f'(from: "{first_year}-01-01T00:00:00Z", to: "{first_year}-12-31T23:59:59Z")')
    for d, count in days:
        if count:
            return date.fromisoformat(d)
    return None


def streaks(days):
    counts = {d: c for d, c in days}
    today = date.today()
    longest = cur = 0
    best_end = None
    for d, c in days:
        cur = cur + 1 if c else 0
        if cur > longest:
            longest, best_end = cur, date.fromisoformat(d)
    end = today if counts.get(today.isoformat(), 0) else today - timedelta(days=1)
    current, day = 0, end
    while counts.get(day.isoformat(), 0):
        current += 1
        day -= timedelta(days=1)
    return current, day + timedelta(days=1), end, longest, \
        (best_end - timedelta(days=longest - 1)) if best_end else None, best_end


def fmt(d, show_year):
    if not d:
        return "—"
    return d.strftime("%b ") + str(d.day) + (d.strftime(", %Y") if show_year else "")


def render(total, first, current, cur_start, cur_end, longest, long_start, long_end):
    width, height = 495, 195
    this_year = date.today().year
    cur_rng = "—" if not current else \
        f"{fmt(cur_start, cur_start.year != this_year)} – {fmt(cur_end, cur_end.year != this_year)}"
    long_rng = "—" if not longest else \
        f"{fmt(long_start, long_start.year != this_year)} – {fmt(long_end, long_end.year != this_year)}"
    total_rng = f"{fmt(first, True)} – Present" if first else ""
    col_w = width / 3
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
             'role="img" aria-label="Contribution streak">',
             "<style>.f{font-family:'Segoe UI',Ubuntu,'Helvetica Neue',Sans-Serif}"
             ".n{font-size:26px;font-weight:700;fill:#ffffff}.l{font-size:12.5px;font-weight:600;fill:#e6e6e6}"
             ".d{font-size:11.5px;fill:#8a8a8a}.i{opacity:0;animation:fade .45s ease-in-out forwards}"
             "@keyframes fade{to{opacity:1}}@media (prefers-reduced-motion:reduce){.i{opacity:1;animation:none}}</style>",
             f'<rect width="{width}" height="{height}" rx="10" fill="#000000"/>']
    cols = [(f"{total:,}", "Total Contributions", total_rng, 0),
            (f"{current:,}", "Current Streak", cur_rng, 150),
            (f"{longest:,}", "Longest Streak", long_rng, 300)]
    for i, (num, label, rng, delay) in enumerate(cols):
        cx = col_w * (i + 0.5)
        if i:
            parts.append(f'<line x1="{col_w * i:.0f}" y1="42" x2="{col_w * i:.0f}" y2="153" stroke="#333333"/>')
        parts.append(f'<g class="i" style="animation-delay:{delay}ms">'
                     f'<text class="f n" x="{cx:.0f}" y="92" text-anchor="middle">{num}</text>'
                     f'<text class="f l" x="{cx:.0f}" y="122" text-anchor="middle">{label}</text>'
                     f'<text class="f d" x="{cx:.0f}" y="146" text-anchor="middle">{rng}</text></g>')
    parts.append("</svg>")
    return "".join(parts)


def main(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    total, days, years = calendar()
    current, cur_start, cur_end, longest, long_start, long_end = streaks(sorted(days))
    first = first_contribution(years)
    (out / "streak.svg").write_text(
        render(total, first, current, cur_start, cur_end, longest, long_start, long_end),
        encoding="utf-8")
    print(f"total={total} current={current} ({cur_start}..{cur_end}) "
          f"longest={longest} ({long_start}..{long_end}) first={first}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dist")
