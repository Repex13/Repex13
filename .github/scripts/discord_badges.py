"""Render one Discord badge strip (SVG) per account into the given folder.

Badges come from dstn.to's full profile when it can see the account; otherwise
from Lanyard's public flags plus Nitro. Icons are embedded so the SVG renders
inside GitHub's image proxy.
"""
import base64
import json
import sys
import urllib.request
from pathlib import Path

ACCOUNTS = {"repexforde": "861006155719770112", "ghostwas": "1070456961310662686"}
UA = {"User-Agent": "Repex13-profile-badges (+https://github.com/Repex13/Repex13)"}
CDN = "https://cdn.discordapp.com/badge-icons/{}.png"
# public_flags bit -> (description, icon), in Discord's display order
FLAGS = {
    0: ("Discord Staff", "5e74e9b61934fc1f67c65515d1f7e60d"),
    1: ("Partnered Server Owner", "3f9748e53446a137a052f3454e2de41e"),
    18: ("Moderator Programs Alumni", "fee1624003e2fee35cb398e125dc479b"),
    2: ("HypeSquad Events", "bf01d1073931f921909045f3a39fd264"),
    6: ("HypeSquad Bravery", "8a88d63823d8a71cd5e390baa45efa02"),
    7: ("HypeSquad Brilliance", "011940fd013da3f7fb926e4a1cd2e618"),
    8: ("HypeSquad Balance", "3aa41de486fa12454c3761e8e223442e"),
    3: ("Discord Bug Hunter", "2717692c7dca7289b35297368a940dd0"),
    14: ("Discord Bug Hunter", "848f79194d4be5ff5f81505cbd0ce1e6"),
    22: ("Active Developer", "6bdc42827a38498929a4920da12695d9"),
    17: ("Early Verified Bot Developer", "6df5892e0f35b051f8b61eace34f4967"),
    9: ("Early Supporter", "7060786766c9c840eb3019e725d2b358"),
}
NITRO = ("Discord Nitro", "2ba85e8026a8614b640c2837bcdfe21b")


def fetch(url, binary=False):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        data = r.read()
    return data if binary else json.loads(data)


def badges_for(user_id):
    lanyard = fetch(f"https://api.lanyard.rest/v1/users/{user_id}")["data"]["discord_user"]
    try:
        profile = fetch(f"https://dcdn.dstn.to/profile/{user_id}")
    except Exception:
        profile = {}
    if profile.get("badges") and not profile.get("private"):
        return [(b["description"], b["icon"]) for b in profile["badges"]]
    flags = lanyard.get("public_flags") or 0
    found = [badge for bit, badge in FLAGS.items() if flags >> bit & 1]
    if (profile.get("premium_type") or 0) > 0 or str(lanyard.get("avatar") or "").startswith("a_"):
        found.append(NITRO)
    return found


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def render(badges):
    size, gap, x = 24, 8, 84
    parts = []
    for description, icon in badges:
        png = base64.b64encode(fetch(CDN.format(icon), binary=True)).decode()
        parts.append(f'<image x="{x}" y="10" width="{size}" height="{size}" href="data:image/png;base64,{png}">'
                     f'<title>{esc(description)}</title></image>')
        x += size + gap
    if not parts:
        parts.append('<text x="84" y="27" fill="#6c7086" font-size="13">no public badges</text>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="410" height="44" viewBox="0 0 410 44" role="img" '
            f'aria-label="Discord badges: {esc(", ".join(d for d, _ in badges) or "none")}">'
            '<rect width="410" height="44" rx="10" fill="#1e1e2e"/>'
            '<g font-family="\'Segoe UI\',Ubuntu,\'Helvetica Neue\',Arial,sans-serif">'
            '<text x="16" y="27" fill="#a6adc8" font-size="13" font-weight="600">badges</text>'
            + "".join(parts) + "</g></svg>")


def main(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, user_id in ACCOUNTS.items():
        badges = badges_for(user_id)
        (out / f"discord-{name}.svg").write_text(render(badges), encoding="utf-8")
        print(name, "->", [d for d, _ in badges])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dist")
