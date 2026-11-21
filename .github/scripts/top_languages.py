"""Render a "most used languages" card from every repo the user owns:
public, private and forks, weighted by GitHub's language byte counts.

Uses the gh CLI, so it reads GH_TOKEN in Actions and the keyring locally.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

USER = "Repex13"
TOP = 8
GRAYS = ["#ffffff", "#d4d4d4", "#a9a9a9", "#858585", "#666666", "#4d4d4d", "#3a3a3a", "#2b2b2b"]
QUERY = """query($login: String!) {
  user(login: $login) {
    repositories(ownerAffiliations: OWNER, first: 100) {
      nodes { languages(first: 50) { edges { size node { name color } } } }
    }
  }
}"""


def languages():
    out = subprocess.run(["gh", "api", "graphql", "-f", f"login={USER}", "-f", f"query={QUERY}"],
                         check=True, capture_output=True, text=True, encoding="utf-8").stdout
    totals, colors = {}, {}
    for repo in json.loads(out)["data"]["user"]["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            totals[name] = totals.get(name, 0) + edge["size"]
            colors[name] = ""
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])
    if len(ranked) > TOP:
        ranked = ranked[:TOP - 1] + [("Other", sum(size for _, size in ranked[TOP - 1:]))]
    for i, (name, _) in enumerate(ranked):
        colors[name] = GRAYS[min(i, len(GRAYS) - 1)]
    return ranked, colors


def readable(color):
    """Lighten colors too dark to see on the card (e.g. PowerShell's navy)."""
    h = color.lstrip("#")
    if len(h) != 6:
        return color
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    if (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255 >= 0.25:
        return color
    return "#" + "".join(f"{round(c + (t - c) * 0.45):02x}" for c, t in zip(rgb, (205, 214, 244)))


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(ranked, colors):
    width, pad, cols, row_h = 990, 25, 4, 30
    total = sum(size for _, size in ranked)
    rows = max(1, math.ceil(len(ranked) / cols))
    height = 96 + (rows - 1) * row_h + 22
    bar_w = width - 2 * pad
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
             f'role="img" aria-label="Most used languages">',
             "<style>.f{font-family:'Segoe UI',Ubuntu,'Helvetica Neue',Sans-Serif}"
             ".t{font-size:18px;font-weight:600;fill:#ffffff}.n{font-size:14px;font-weight:600;fill:#e6e6e6}"
             ".p{font-size:13px;fill:#8a8a8a}.i{opacity:0;animation:fade .45s ease-in-out forwards}"
             "@keyframes fade{to{opacity:1}}@media (prefers-reduced-motion:reduce){.i{opacity:1;animation:none}}</style>",
             f'<rect width="{width}" height="{height}" rx="10" fill="#000000"/>',
             f'<text class="f t" x="{pad}" y="38">Most Used Languages</text>']
    if not total:
        parts.append(f'<text class="f p" x="{pad}" y="72">No languages data.</text></svg>')
        return "".join(parts)
    parts.append(f'<clipPath id="bar"><rect x="{pad}" y="54" width="{bar_w}" height="10" rx="5"/></clipPath><g clip-path="url(#bar)">')
    x = float(pad)
    for name, size in ranked:
        w = bar_w * size / total
        parts.append(f'<rect x="{x:.2f}" y="54" width="{max(w - 2, 0.5):.2f}" height="10" fill="{colors[name]}"/>')
        x += w
    parts.append("</g>")
    col_w = bar_w / cols
    for i, (name, size) in enumerate(ranked):
        cx, cy = pad + (i % cols) * col_w, 96 + (i // cols) * row_h
        parts.append(f'<g class="i" style="animation-delay:{150 + i * 120}ms">'
                     f'<circle cx="{cx + 6:.1f}" cy="{cy - 5}" r="6" fill="{colors[name]}" stroke="#9a9a9a" stroke-width=".8"/>'
                     f'<text class="f n" x="{cx + 20:.1f}" y="{cy}">{esc(name)} <tspan class="p">{100 * size / total:.1f}%</tspan></text></g>')
    parts.append("</svg>")
    return "".join(parts)


def main(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ranked, colors = languages()
    (out / "top-languages.svg").write_text(render(ranked, colors), encoding="utf-8")
    total = sum(s for _, s in ranked) or 1
    print(", ".join(f"{n} {100 * s / total:.1f}%" for n, s in ranked))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dist")
