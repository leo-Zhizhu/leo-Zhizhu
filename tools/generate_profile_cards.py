#!/usr/bin/env python3
"""Generate the profile README graphics as light/dark SVG pairs in profile/.

Everything the README shows as a "card" is produced here so the wording, the
numbers and the palette live in exactly one place. Run:

    python3 tools/generate_profile_cards.py

GitHub strips inline `style=` attributes from README HTML, so colour in the
README has to come from images. Each card is emitted twice -- once per theme --
and the README picks between them with <picture media="(prefers-color-scheme)">.

Palette note: the accent hexes below were checked against the data-viz
colour gates (lightness band, chroma floor, CVD separation, contrast vs the
page surface) for their own theme. Re-validate before changing them.
"""

from __future__ import annotations

import os
import string

W = 880  # card width; GitHub's README column is ~896px

SANS = ("ui-sans-serif,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,"
        "'Helvetica Neue',Arial,sans-serif")
MONO = ("ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
        "'Liberation Mono',monospace")

THEMES = {
    "light": {
        "panel": "#f6f8fa", "inner": "#ffffff", "border": "#d0d7de",
        "text": "#1f2328", "muted": "#59636e", "faint": "#818b98",
        "track": "#d8dee4", "chip": "#eaeef2", "rule": "#d8dee4",
        "cyan": "#0782a2", "amber": "#b45309",
        "violet": "#6d28d9", "rose": "#be123c",
    },
    "dark": {
        "panel": "#161b22", "inner": "#0d1117", "border": "#30363d",
        "text": "#e6edf3", "muted": "#9198a1", "faint": "#6e7681",
        "track": "#30363d", "chip": "#21262d", "rule": "#30363d",
        "cyan": "#1596b0", "amber": "#c98500",
        "violet": "#9085e9", "rose": "#e66767",
    },
}

# ---------------------------------------------------------------- primitives

_NARROW = set("iljtIfr.,:;'|!()[]{}-` ")
_WIDE = set("mwMW@%")
_UPPER = set(string.ascii_uppercase)


def tw(s: str, size: float, bold: bool = False, mono: bool = False) -> float:
    """Approximate rendered text width. Used to size pills and centre boxes."""
    if mono:
        return len(s) * size * 0.6
    total = 0.0
    for ch in s:
        if ch == " ":
            total += 0.27
        elif ch in _NARROW:
            total += 0.31
        elif ch in _WIDE:
            total += 0.85
        elif ch in _UPPER:
            total += 0.66
        elif ch.isdigit():
            total += 0.56
        else:
            total += 0.53
    return total * size * (1.05 if bold else 1.0)


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def txt(x, y, s, size=13, fill="#000", bold=False, anchor="start",
        mono=False, opacity=None, spacing=None):
    weight = ' font-weight="600"' if bold else ""
    op = f' opacity="{opacity}"' if opacity is not None else ""
    ls = f' letter-spacing="{spacing}"' if spacing is not None else ""
    fam = MONO if mono else SANS
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" '
            f'font-size="{size}"{weight} fill="{fill}" '
            f'text-anchor="{anchor}"{op}{ls}>{esc(s)}</text>')


def rect(x, y, w, h, fill, rx=0, stroke=None, sw=1, opacity=None):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    op = f' opacity="{opacity}"' if opacity is not None else ""
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" '
            f'height="{h:.1f}" rx="{rx}" fill="{fill}"{st}{op}/>')


def panel(t, h, title):
    """Outer rounded card, transparent outside so it floats on the page."""
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" '
        f'viewBox="0 0 {W} {h}" role="img" aria-label="{esc(title)}">',
        f'<title>{esc(title)}</title>',
        rect(0.5, 0.5, W - 1, h - 1, t["panel"], rx=12, stroke=t["border"]),
    ]


def stripe(t, h, colour):
    """Accent bar down the left edge, clipped to the card's rounded corner."""
    return (f'<clipPath id="cc"><rect x="0" y="0" width="{W}" height="{h}" '
            f'rx="12"/></clipPath>'
            f'<g clip-path="url(#cc)">{rect(0, 0, 5, h, colour)}</g>')


def chip(t, x, y, label, size=11.5, pad=11, h=22, fill=None, colour=None):
    """Pill with centred text. Returns (svg, width)."""
    w = tw(label, size, bold=True) + pad * 2
    body = rect(x, y, w, h, fill or t["chip"], rx=h / 2)
    body += txt(x + w / 2, y + h / 2 + size * 0.36, label, size,
                colour or t["muted"], bold=True, anchor="middle")
    return body, w


def arrow(t, x1, x2, y):
    """Short connector with a solid head, drawn without <marker>."""
    tip = x2
    return (f'<path d="M{x1:.1f} {y} H{tip - 6:.1f}" stroke="{t["faint"]}" '
            f'stroke-width="1.5" fill="none"/>'
            f'<path d="M{tip:.1f} {y} l-6.5,-4 v8 z" fill="{t["faint"]}"/>')


def flow(t, cy, nodes, accent):
    """Centred pipeline of two-line boxes joined by arrows."""
    bh, gap, pad = 46, 24, 15
    widths = []
    for top, bot in nodes:
        widths.append(max(tw(top, 11.5, bold=True), tw(bot, 10.5)) + pad * 2)
    total = sum(widths) + gap * (len(nodes) - 1)
    x = (W - total) / 2
    out = []
    for i, (top, bot) in enumerate(nodes):
        w = widths[i]
        out.append(rect(x, cy - bh / 2, w, bh, t["inner"], rx=8,
                        stroke=t["border"]))
        out.append(rect(x, cy - bh / 2, w, 2.5, accent, rx=1.2))
        out.append(txt(x + w / 2, cy - 2, top, 11.5, t["text"], bold=True,
                       anchor="middle"))
        out.append(txt(x + w / 2, cy + 14, bot, 10.5, t["muted"],
                       anchor="middle"))
        if i < len(nodes) - 1:
            out.append(arrow(t, x + w + 5, x + w + gap - 5, cy))
        x += w + gap
    return out


def tiles(t, y, items, accent):
    """Evenly spaced value/label stat tiles with hairline separators."""
    out = []
    x0, span = 28, W - 56
    step = span / len(items)
    for i, (value, label) in enumerate(items):
        cx = x0 + step * i + step / 2
        out.append(txt(cx, y, value, 19, accent, bold=True, anchor="middle"))
        out.append(txt(cx, y + 18, label, 10.8, t["muted"], anchor="middle"))
        if i:
            lx = x0 + step * i
            out.append(f'<path d="M{lx:.1f} {y - 16} V{y + 24}" '
                       f'stroke="{t["rule"]}" stroke-width="1"/>')
    return out


# -------------------------------------------------------------------- cards

def hero(t):
    # The role line stays domain-level on purpose: no single employer should
    # define the card. Breadth comes from the contexts line, proof from the
    # stat column, and specificity from the chips.
    h = 220
    s = panel(t, h, "Zhu (Leo) Zhi - machine learning and systems engineer")
    s.append(stripe(t, h, t["cyan"]))

    s.append(txt(34, 40, "CORNELL CS '28   ·   GPA 4.0 / 4.0", 10.5,
                 t["faint"], bold=True, spacing="1.4"))
    s.append(txt(32, 84, "Zhu (Leo) Zhi", 38, t["text"], bold=True))
    s.append(txt(34, 112, "Machine Learning Systems · Distributed "
                 "Infrastructure · AI Agents", 15.5, t["cyan"], bold=True))
    s.append(txt(34, 138, "I build the parts that have to keep working "
                 "— on a vehicle, in a cluster, inside an agent loop.",
                 12.5, t["muted"]))
    s.append(txt(34, 160, "Code in production on an autonomy fleet, in a "
                 "54-node cluster, and in a platform 5,000+ people use.",
                 11.5, t["faint"]))

    x = 34
    for label, key in [("On-vehicle inference", "cyan"), ("Kubernetes at "
                       "scale", "amber"), ("Agent infrastructure", "violet"),
                       ("Robotics", "rose")]:
        body, w = chip(t, x, 182, label, colour=t[key])
        s.append(body)
        x += w + 8

    s.append(f'<path d="M574 34 V186" stroke="{t["rule"]}" stroke-width="1"/>')
    stats = [("161×", "faster city-scale simulation", "cyan"),
             ("-70%", "fleet upload volume, shipped", "amber"),
             ("1.6k", "GitHub stars · 5,000+ users", "violet")]
    y = 76
    for value, label, key in stats:
        s.append(txt(692, y, value, 23, t[key], bold=True, anchor="end"))
        s.append(txt(706, y - 1, label, 11, t["muted"]))
        y += 46
    return h, s


def impact(t):
    rows = [
        ("City-scale simulation run", "Unity raycasting, Manhattan",
         30 * 3600, 669, "30 h", "11 min", "161× faster"),
        ("PostGIS spatial query", "after index + memory retune",
         2000, 25, "2,000 ms", "25 ms", "80× faster"),
        ("Fleet data uploaded", "per vehicle, per day",
         100, 30, "100%", "30%", "70% less"),
        ("Agent context overhead", "per LLM call, tool schemas",
         10000, 300, "10k tok", "~0", "10k saved"),
        ("Web interaction latency", "INP, chat workspace",
         140, 40, "140 ms", "40 ms", "3.5× faster"),
        ("AUV steady-state error", "6-DoF controller, pool tests",
         100, 20, "baseline", "20%", "80% less"),
    ]
    row_h, top = 50, 92
    h = top + row_h * len(rows) + 22
    s = panel(t, h, "Before and after: workloads I made faster or smaller")
    s.append(stripe(t, h, t["cyan"]))

    s.append(txt(32, 42, "Same workload, before and after the change. "
                "Shorter is better.", 12.5, t["muted"]))

    # legend -- two series, so identity is never colour-alone
    lx = W - 32
    for label, colour in [("after", t["cyan"]), ("before", t["track"])]:
        wl = tw(label, 11)
        s.append(txt(lx, 46, label, 11, t["muted"], anchor="end"))
        s.append(rect(lx - wl - 16, 39, 10, 7, colour, rx=3.5))
        lx -= wl + 32

    bx, bw = 258, 358
    for i, (name, ctx, before, after, bl, al, factor) in enumerate(rows):
        y = top + row_h * i
        s.append(txt(32, y + 6, name, 13, t["text"], bold=True))
        s.append(txt(32, y + 22, ctx, 10.8, t["faint"]))
        ratio = max(after / before, 0.0)
        aw = max(ratio * bw, 7)
        s.append(rect(bx, y - 6, bw, 9, t["track"], rx=4.5))
        s.append(rect(bx, y + 9, aw, 9, t["cyan"], rx=4.5))
        s.append(txt(bx + bw + 16, y + 6, f"{bl} → {al}", 11.5,
                     t["muted"], mono=True))
        s.append(txt(W - 32, y + 6, factor, 13.5, t["cyan"], bold=True,
                     anchor="end"))
        if i < len(rows) - 1:
            s.append(f'<path d="M32 {y + 32} H{W - 32}" stroke="{t["rule"]}" '
                     f'stroke-width="1" opacity="0.55"/>')
    return h, s


def project(t, accent_key, title, meta, hook, badges, nodes, stats, label):
    h = 250
    accent = t[accent_key]
    s = panel(t, h, label)
    s.append(stripe(t, h, accent))

    s.append(txt(32, 46, title, 19, accent, bold=True))
    s.append(txt(32, 68, meta, 11.5, t["faint"], mono=True))
    s.append(txt(32, 94, hook, 13, t["text"]))

    x = W - 32
    for text_, filled in reversed(badges):
        body, w = chip(t, 0, 0, text_, size=11, h=21,
                       fill=accent if filled else t["chip"],
                       colour=t["inner"] if filled else t["muted"])
        x -= w
        s.append(f'<g transform="translate({x:.1f},31)">{body}</g>')
        x -= 7

    s.extend(flow(t, 148, nodes, accent))
    s.append(f'<path d="M28 192 H{W - 28}" stroke="{t["rule"]}" '
             f'stroke-width="1"/>')
    s.extend(tiles(t, 218, stats, accent))
    return h, s


def bonsai(t):
    return project(
        t, "cyan",
        "On-Vehicle Data Curation Pipeline",
        "Bonsai Robotics  ·  C++ / ROS 2  ·  private repo  ·  merged to main, "
        "running on every vehicle",
        "A fleet records far more than anyone can upload, so the vehicle "
        "itself decides what is worth sending home.",
        [("private", False), ("C++ / ROS 2", True)],
        [("sensor stream", "MCAP recordings"),
         ("4 scorers", "density · semantics"),
         ("window score", "anomaly · motion"),
         ("upload gate", "race-free finalize"),
         ("cloud", "top windows only")],
        [("-70%", "upload volume"), ("8×", "usable score spread"),
         ("<3%", "latency for a distilled VLM"),
         ("287k", "frames embedded on Ray")],
        "Bonsai Robotics on-vehicle data curation pipeline")


def langalpha(t):
    return project(
        t, "violet",
        "LangAlpha — Claude Code for financial markets",
        "Ginlix AI  ·  Python · LangGraph · Postgres · Redis  ·  full-stack "
        "owner, CI/CD to incident response",
        "Chat rebuilt as a persistent workspace, so research compounds across "
        "sessions instead of resetting at every prompt.",
        [("5,000+ users", False), ("1.6k stars", True)],
        [("web · slack · cli", "one workspace"),
         ("agent core", "PTC + subagent swarm"),
         ("sandbox", "Daytona isolation"),
         ("durable state", "Postgres + Redis"),
         ("30+ tools", "native + MCP")],
        [("-10k", "tokens per agent call"), ("140→40ms", "interaction latency"),
         ("30+", "tools routed by cost"), ("1.6k", "GitHub stars")],
        "LangAlpha agent harness architecture")


def sunlight(t):
    return project(
        t, "amber",
        "SunlightCity — 7.89B sunlight measurements in 11 minutes",
        "Cornell Ezra Systems  ·  Unity · Kubernetes · PostGIS  ·  "
        "simulation infrastructure lead",
        "Sun or shadow, at every street position and every minute — answered "
        "7.89 billion times so a router can query it instantly.",
        [("500 GB output", False), ("161× speedup", True)],
        [("Unity mesh", "Manhattan model"),
         ("headless build", "IL2CPP raycaster"),
         ("54 workers", "Kubernetes fleet"),
         ("9 shards", "PostGIS cluster"),
         ("11m 09s", "inside a 15m deadline")],
        [("161×", "vs one machine"), ("16M/s", "rows into Postgres"),
         ("2000→25ms", "spatial queries"),
         ("54 & 9", "sized by a capacity model")],
        "SunlightCity distributed simulation pipeline")


def stack(t):
    groups = [
        ("cyan", "Languages",
         ["Python", "C++", "Java", "Go", "Kotlin", "C#", "TypeScript", "SQL"]),
        ("violet", "ML & Agents",
         ["PyTorch", "ROS 2", "OpenCV", "LangGraph", "LangChain", "MCP",
          "Ray / Anyscale"]),
        ("amber", "Backend & Data",
         ["Spring Boot", "FastAPI", "Node.js", "React", "PostgreSQL",
          "PostGIS", "Redis", "Elasticsearch"]),
        ("rose", "Infrastructure",
         ["Docker", "Kubernetes", "AWS", "Unity headless", "CI/CD", "Linux"]),
    ]
    row_h, top = 46, 62
    h = top + row_h * len(groups) + 12
    s = panel(t, h, "Technical stack by area")
    s.append(stripe(t, h, t["violet"]))
    s.append(txt(32, 42, "Grouped by where I actually use it, not by "
                "how many tutorials I have read.", 12.5, t["muted"]))

    for i, (key, name, items) in enumerate(groups):
        y = top + row_h * i
        s.append(f'<circle cx="36" cy="{y + 10}" r="4.5" fill="{t[key]}"/>')
        s.append(txt(48, y + 14, name, 12.5, t["text"], bold=True))
        x = 172
        for item in items:
            body, w = chip(t, x, y - 2, item, size=11, h=24,
                           colour=t["text"])
            s.append(body)
            x += w + 7
    return h, s


CARDS = {
    "hero": hero,
    "impact": impact,
    "card-bonsai": bonsai,
    "card-langalpha": langalpha,
    "card-sunlightcity": sunlight,
    "stack": stack,
}


def main() -> None:
    out = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "profile")
    os.makedirs(out, exist_ok=True)
    for name, build in CARDS.items():
        for mode, theme in THEMES.items():
            h, parts = build(theme)
            svg = "\n".join(parts) + "\n</svg>\n"
            path = os.path.join(out, f"{name}-{mode}.svg")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(svg)
            print(f"wrote {path} ({W}x{h})")


if __name__ == "__main__":
    main()
