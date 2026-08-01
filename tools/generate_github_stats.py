#!/usr/bin/env python3
"""Render profile/github-{light,dark}.svg from the GitHub REST API.

Replaces the third-party stats/top-language cards, which depend on a shared
hosted instance that rate-limits (503) and on a token scope GITHUB_TOKEN does
not have ("Resource not accessible by integration") -- both of which end up
committing a "Something went wrong!" card to the repo.

Everything here comes from the public REST API, so it works unauthenticated;
set GITHUB_TOKEN to get the higher rate limit in CI.

A successful run snapshots its numbers to profile/github-stats.json. If the API
refuses a request the run rebuilds from that snapshot instead of shipping a card
assembled from a half-finished fetch -- an unauthenticated run hits the 60/hour
limit partway through and would otherwise report a star total missing every repo
it never reached.

    python3 tools/generate_github_stats.py [user]
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

from generate_profile_cards import (THEMES, W, panel, rect, stripe, tiles,
                                    tw, txt)

USER = "leo-Zhizhu"

# Repos I build in an org rather than under my own account. Counted in the
# star total; without them the number understates the work by ~1.6k.
EXTRA_REPOS = ["ginlix-ai/LangAlpha"]

# Languages the byte counts over-weight relative to the work they represent.
SKIP_LANGS = {"HTML", "CSS", "Shell", "Dockerfile", "Makefile", "CMake",
              "Jupyter Notebook", "Batchfile", "Roff", "SCSS"}

# Reference categorical order -- validated for adjacent pairs in both modes,
# which is the pairlist a stacked bar uses.
SERIES = {
    "light": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4",
              "#4a3aa7", "#8c959f"],
    "dark": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181",
             "#9085e9", "#6e7681"],
}
TOP_N = 5


class Unavailable(Exception):
    """The API refused the request -- rate limit, auth, or an outage."""


def api(path: str):
    """Fetch JSON. Returns None only for a genuine 404."""
    url = path if path.startswith("http") else f"https://api.github.com{path}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "leo-Zhizhu-profile-cards",
    })
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return None
        # 403/429 is the unauthenticated rate limit. Swallowing it here is how
        # a half-fetched, badly wrong card gets rendered -- stars silently drop
        # to whatever was collected before the limit hit. Abort instead.
        raise Unavailable(f"{url} -> HTTP {err.code}") from err
    except (urllib.error.URLError, TimeoutError) as err:
        raise Unavailable(f"{url} -> {err}") from err


def collect(user: str) -> dict:
    profile = api(f"/users/{user}")
    repos = api(f"/users/{user}/repos?per_page=100&type=owner")
    own = [r for r in repos if not r["fork"]]

    stars = sum(r["stargazers_count"] for r in own)
    langs: dict[str, int] = {}

    def add_languages(url: str) -> None:
        for name, count in (api(url) or {}).items():
            if name not in SKIP_LANGS:
                langs[name] = langs.get(name, 0) + count

    for repo in own:
        add_languages(repo["languages_url"])

    extra = 0
    for full_name in EXTRA_REPOS:
        data = api(f"/repos/{full_name}")
        if data is None:
            raise Unavailable(f"{full_name} is gone; the star total would be "
                              "wrong without it")
        extra += data["stargazers_count"]
        add_languages(data["languages_url"])

    ordered = sorted(langs.items(), key=lambda kv: -kv[1])
    distinct = len(ordered)
    top = ordered[:TOP_N]
    rest = sum(c for _, c in ordered[TOP_N:])
    if rest:
        top.append(("Other", rest))
    total = sum(c for _, c in top) or 1

    return {
        "repos": len(own),
        "stars": stars + extra,
        "followers": profile.get("followers", 0),
        "distinct_languages": distinct,
        "languages": [(n, c / total) for n, c in top],
    }


def human(n: int) -> str:
    return f"{n / 1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def card(t, mode, data):
    h = 220
    s = panel(t, h, "GitHub at a glance")
    s.append(stripe(t, h, t["cyan"]))

    s.append(txt(32, 42, "Public repositories I own, plus the org repo I ship "
                "day to day.", 12.5, t["muted"]))

    s.extend(tiles(t, 88, [
        (human(data["stars"]), "stars earned"),
        (str(data["repos"]), "public repos"),
        (str(data["followers"]), "followers"),
        (str(data["distinct_languages"]), "languages in use"),
    ], t["cyan"]))

    s.append(f'<path d="M28 128 H{W - 28}" stroke="{t["rule"]}" '
             f'stroke-width="1"/>')
    s.append(txt(32, 156, "Language mix, by bytes of code", 11.5, t["faint"]))

    # Stacked bar: 2px surface gap between segments keeps them separable
    # without a stroke, and every segment is also named in the legend.
    bar_y, bar_h, x0, span = 166, 12, 32, W - 64
    palette = SERIES[mode]
    x = x0
    for i, (_, share) in enumerate(data["languages"]):
        seg = max(span * share - 2, 3)
        s.append(rect(x, bar_y, seg, bar_h, palette[i % len(palette)], rx=3))
        x += seg + 2

    lx = 32
    for i, (name, share) in enumerate(data["languages"]):
        label = f"{name} {share * 100:.0f}%"
        s.append(f'<circle cx="{lx + 4:.1f}" cy="202" r="4.5" '
                 f'fill="{palette[i % len(palette)]}"/>')
        s.append(txt(lx + 14, 206, label, 11, t["muted"]))
        lx += 14 + tw(label, 11) + 20
    return h, s


def main() -> None:
    user = sys.argv[1] if len(sys.argv) > 1 else USER
    out = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "profile")
    cache = os.path.join(out, "github-stats.json")

    try:
        data = collect(user)
        os.makedirs(out, exist_ok=True)
        with open(cache, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
    except Unavailable as err:
        # Re-render from the last good snapshot rather than shipping a card
        # built from a half-finished fetch.
        if not os.path.exists(cache):
            print(f"github api unavailable ({err}) and no cached snapshot; "
                  "leaving existing cards alone", file=sys.stderr)
            raise SystemExit(1)
        print(f"github api unavailable ({err}); rebuilding from {cache}",
              file=sys.stderr)
        with open(cache, encoding="utf-8") as fh:
            data = json.load(fh)

    for mode, theme in THEMES.items():
        h, parts = card(theme, mode, data)
        path = os.path.join(out, f"github-{mode}.svg")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(parts) + "\n</svg>\n")
        print(f"wrote {path} ({W}x{h})")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
