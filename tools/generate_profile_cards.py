#!/usr/bin/env python3
"""Generate the profile README graphics into profile/.

Everything the README shows as a "card" is produced here so the wording, the
numbers and the palette live in exactly one place. Run:

    python3 tools/generate_profile_cards.py

GitHub strips inline `style=` attributes from README HTML, so colour in the
README has to come from images.

Visual style: retro-futurist terminal. Near-black surfaces, one blue accent,
4x4 Bayer dithering instead of gradients, CRT scanlines, film grain, and ASCII
rain on the hero. The palette is a single dark skin -- there is no light
surface in it, so the cards are theme-independent and the README embeds them
directly rather than switching on prefers-color-scheme.

Contrast, measured against the #121212 card surface:
    #8b8b8b 5.5:1 body   #3b82f6 5.1:1 small accent text
    #2563eb 3.6:1 fills and large numerals only -- never small type
    #585858 2.6:1 and #333333 1.5:1 are structure, never text
"""

from __future__ import annotations

import math
import os
import random
import string

W = 880  # card width; GitHub's README column is ~896px

SANS = ("ui-sans-serif,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,"
        "'Helvetica Neue',Arial,sans-serif")
MONO = ("ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
        "'Liberation Mono',monospace")

T = {
    "bg": "#0f0f0f",        # recessed wells: node boxes, chips
    "panel": "#121212",     # card surface
    "border": "#333333",
    "rule": "#333333",
    "track": "#333333",
    "faint": "#585858",     # hairlines and decoration
    "muted": "#8b8b8b",     # body text
    "text": "#e8e8e8",      # headings
    "accent": "#2563eb",    # fills, bars, large numerals
    "accent_text": "#3b82f6",  # the same blue, lifted for small type
}

# ---------------------------------------------------------------- primitives

_NARROW = set("iljtIfr.,:;'|!()[]{}-` ")
_WIDE = set("mwMW@%")
_UPPER = set(string.ascii_uppercase)


def tw(s: str, size: float, bold: bool = False, mono: bool = True) -> float:
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


# ------------------------------------------------------------------ texture

# 4x4 ordered (Bayer) matrix. A level of k fills the cells below k, giving
# k/16 coverage -- the classic way to fake a tone on a display that has none.
BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))
DITHER_LEVELS = (1, 2, 3, 4, 6, 8, 10, 12, 14)
DITHER_INKS = {"a": T["accent"], "g": T["faint"], "d": T["border"],
               "m": T["muted"]}


def dither(level: int, ink: str = "a") -> str:
    """Fill reference for a dithered tone, e.g. fill=dither(8)."""
    return f"url(#dt{level}{ink})"


def _dither_defs() -> str:
    out = []
    for ink, colour in DITHER_INKS.items():
        for level in DITHER_LEVELS:
            cells = "".join(
                f'<rect x="{c}" y="{r}" width="1" height="1" fill="{colour}"/>'
                for r in range(4) for c in range(4) if BAYER[r][c] < level)
            out.append(f'<pattern id="dt{level}{ink}" width="4" height="4" '
                       f'patternUnits="userSpaceOnUse">{cells}</pattern>')
    return "".join(out)


def dither_rule(x, y, w, level=6, ink="d", h=2):
    """A divider drawn as a dithered band instead of a solid hairline."""
    return rect(x, y, w, h, dither(level, ink))


def dither_ramp(x, y, w, steps=4, step_h=3, ink="d", top=10):
    """Tone ramp: dense at the top, thinning downward. Fakes a gradient."""
    out = []
    for i in range(steps):
        level = max(1, int(top * (1 - i / steps)))
        out.append(rect(x, y + i * step_h, w, step_h, dither(level, ink)))
    return "".join(out)


RAIN_CHARS = ("01<>/\\|=+*#%&$@~^:;.-_[]{}()"
              "ABCDEFGHJKLMNPQRSTUVWXYZ0123456789")


def ascii_rain(x, y, w, h, seed, col_w=11, line_h=13):
    """Columns of falling glyphs. Deterministic: same seed, same output, so
    regenerating the cards does not churn the diff."""
    rnd = random.Random(seed)
    cols, rows = int(w // col_w), int(h // line_h)
    out = []
    for c in range(cols):
        cx = x + c * col_w
        head = rnd.randrange(-6, rows + 6)
        spans = []
        for r in range(rows):
            ch = rnd.choice(RAIN_CHARS)
            behind = head - r
            if behind < 0:
                colour, op = T["border"], 0.55
            elif behind == 0:
                colour, op = T["accent_text"], 0.95
            elif behind < 4:
                colour, op = T["muted"], 0.60
            elif behind < 9:
                colour, op = T["faint"], 0.45
            else:
                colour, op = T["border"], 0.65
            spans.append(f'<tspan x="{cx:.1f}" dy="{line_h}" fill="{colour}" '
                         f'opacity="{op}">{esc(ch)}</tspan>')
        out.append(f'<text y="{y - line_h:.1f}" font-family="{MONO}" '
                   f'font-size="10.5">{"".join(spans)}</text>')
    return "".join(out)


# -------------------------------------------------------------------- frame

def panel(h, title, rain=None):
    """Card shell: surface, hairline border, corner brackets, optional rain.

    Returns the opening fragments; overlay() closes the look on top.
    """
    defs = (f'<defs>{_dither_defs()}'
            f'<clipPath id="card"><rect x="0" y="0" width="{W}" height="{h}" '
            f'rx="3"/></clipPath>'
            f'<pattern id="scan" width="1" height="3" '
            f'patternUnits="userSpaceOnUse">'
            f'<rect width="1" height="1" fill="#000000" opacity="0.5"/>'
            f'</pattern>'
            f'<filter id="grain" x="0" y="0" width="100%" height="100%">'
            f'<feTurbulence type="fractalNoise" baseFrequency="0.9" '
            f'numOctaves="2" stitchTiles="stitch"/>'
            f'<feColorMatrix type="saturate" values="0"/></filter>'
            f'<linearGradient id="rainfade" x1="0" y1="0" x2="1" y2="0">'
            f'<stop offset="0" stop-color="#fff" stop-opacity="0.85"/>'
            f'<stop offset="0.38" stop-color="#fff" stop-opacity="0"/>'
            f'<stop offset="0.62" stop-color="#fff" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="#fff" stop-opacity="0.85"/>'
            f'</linearGradient>'
            f'<mask id="rainmask"><rect width="{W}" height="{h}" '
            f'fill="url(#rainfade)"/></mask></defs>')

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" '
        f'viewBox="0 0 {W} {h}" role="img" aria-label="{esc(title)}">',
        f'<title>{esc(title)}</title>',
        defs,
        rect(0, 0, W, h, T["panel"], rx=3),
    ]
    if rain:
        parts.append(f'<g clip-path="url(#card)" mask="url(#rainmask)" '
                     f'opacity="0.85">{rain}</g>')
    parts.append(rect(0.5, 0.5, W - 1, h - 1, "none", rx=3,
                      stroke=T["border"]))
    parts.append(corners(h))
    return parts


def corners(h, inset=7, arm=9):
    """Crop-mark brackets at the four corners."""
    c, o = T["faint"], inset
    pts = [(o, o, 1, 1), (W - o, o, -1, 1), (o, h - o, 1, -1),
           (W - o, h - o, -1, -1)]
    return "".join(
        f'<path d="M{x} {y + arm * sy} V{y} H{x + arm * sx}" stroke="{c}" '
        f'stroke-width="1" fill="none"/>' for x, y, sx, sy in pts)


def stripe(h, colour=None):
    """Left rule: solid accent at the top, dithering out toward the bottom."""
    solid = min(h * 0.42, 120)
    body = rect(0, 0, 4, solid, colour or T["accent"])
    y = solid
    for level in (12, 8, 5, 3, 2):
        body += rect(0, y, 4, (h - solid) / 5, dither(level))
        y += (h - solid) / 5
    return f'<g clip-path="url(#card)">{body}</g>'


def overlay(h):
    """Scanlines and grain are applied in raster by tools/render_cards.py,
    which does them far better than SVG can -- real phosphor bloom, a
    sub-pixel RGB split, and Bayer quantisation to the palette. The SVG stays
    the clean vector source; the PNG beside it is what the README embeds."""
    return ""


def chip(x, y, label, size=11, pad=10, h=21, fill=None, colour=None,
         border=None):
    """Squared-off tag. Returns (svg, width)."""
    w = tw(label, size, bold=True) + pad * 2
    body = rect(x, y, w, h, fill or T["bg"], rx=2,
                stroke=border or T["border"])
    body += txt(x + w / 2, y + h / 2 + size * 0.36, label, size,
                colour or T["muted"], bold=True, anchor="middle", mono=True)
    return body, w


def arrow(x1, x2, y):
    """Short connector with a solid head, drawn without <marker>."""
    return (f'<path d="M{x1:.1f} {y} H{x2 - 6:.1f}" stroke="{T["faint"]}" '
            f'stroke-width="1" fill="none"/>'
            f'<path d="M{x2:.1f} {y} l-5.5,-3.5 v7 z" fill="{T["faint"]}"/>')


def varrow(x, y1, y2, label=None):
    """Vertical connector, head at y2. Label sits to the right of the shaft."""
    down = y2 > y1
    base = y2 - 7 if down else y2 + 7
    out = (f'<path d="M{x:.1f} {y1} V{base:.1f}" stroke="{T["faint"]}" '
           f'stroke-width="1" fill="none" stroke-dasharray="3 2"/>'
           f'<path d="M{x:.1f} {y2} l-3.5,{-7 if down else 7} h7 z" '
           f'fill="{T["faint"]}"/>')
    if label:
        out += txt(x + 9, (y1 + y2) / 2 + 3.5, label, 9.5, T["faint"],
                   mono=True)
    return out


def node_box(x, cy, w, top, bot, bh=46, dashed=False):
    dash = ' stroke-dasharray="4 3"' if dashed else ""
    body = (f'<rect x="{x:.1f}" y="{cy - bh / 2:.1f}" width="{w:.1f}" '
            f'height="{bh}" rx="2" fill="{T["bg"]}" '
            f'stroke="{T["border"]}" stroke-width="1"{dash}/>')
    body += rect(x, cy - bh / 2, w, 2, T["accent"] if not dashed
                 else dither(8))
    body += txt(x + w / 2, cy - 2, top, 11, T["text"], bold=True,
                anchor="middle", mono=True)
    body += txt(x + w / 2, cy + 13, bot, 9.5, T["muted"], anchor="middle",
                mono=True)
    return body


def layout_flow(nodes, gap=22, pad=15):
    """Widths and x positions for a centred pipeline. Returns [(x, w), ...]."""
    widths = [max(tw(top, 11, bold=True), tw(bot, 9.5)) + pad * 2
              for top, bot in nodes]
    x = (W - (sum(widths) + gap * (len(nodes) - 1))) / 2
    placed = []
    for w in widths:
        placed.append((x, w))
        x += w + gap
    return placed


def flow(cy, nodes, gap=22):
    """Centred pipeline of two-line boxes joined by arrows."""
    placed = layout_flow(nodes, gap=gap)
    out = []
    for i, ((x, w), (top, bot)) in enumerate(zip(placed, nodes)):
        out.append(node_box(x, cy, w, top, bot))
        if i < len(nodes) - 1:
            out.append(arrow(x + w + 4, x + w + gap - 4, cy))
    return out


def tiles(y, items):
    """Evenly spaced value/label stat tiles with dithered separators."""
    out = []
    x0, span = 28, W - 56
    step = span / len(items)
    for i, (value, label) in enumerate(items):
        cx = x0 + step * i + step / 2
        out.append(txt(cx, y, value, 19, T["accent_text"], bold=True,
                       anchor="middle", mono=True))
        out.append(txt(cx, y + 17, label, 10, T["muted"], anchor="middle",
                       mono=True))
        if i:
            lx = x0 + step * i
            out.append(rect(lx, y - 16, 1, 40, dither(8, "d")))
    return out


# -------------------------------------------------------------------- cards

def hero():
    # Deliberately spare: identity, the three disciplines, and the reason.
    # Numbers and project detail live in the sections below, not up here.
    h = 214
    cx = W / 2
    s = panel(h, "Zhu (Leo) Zhi - software, machine learning and "
                 "robotics engineer",
              rain=ascii_rain(0, 0, W, h, seed=7301))
    s.append(stripe(h))

    s.append(txt(cx, 46, "CORNELL CS '28   ·   GPA 4.0 / 4.0", 10.5,
                 T["faint"], bold=True, anchor="middle", mono=True,
                 spacing="1.6"))
    s.append(txt(cx, 92, "Zhu (Leo) Zhi", 40, T["text"], bold=True,
                 anchor="middle"))

    roles = ["Software Engineer", "Machine Learning Engineer",
             "Robotics Engineer"]
    widths = [tw(label, 11, bold=True) + 26 for label in roles]
    x = cx - (sum(widths) + 10 * (len(roles) - 1)) / 2
    for label, w in zip(roles, widths):
        body, _ = chip(x, 116, label, size=11, pad=13, h=24,
                       colour=T["accent_text"], border=T["accent"])
        s.append(body)
        x += w + 10

    s.append(dither_rule(cx - 90, 154, 180, level=6))
    s.append(txt(cx, 178, "However the technical landscape shifts, "
                 "engineering keeps returning to one origin:", 12.5,
                 T["muted"], anchor="middle"))
    s.append(txt(cx, 196, "making things that solve real problems — with a "
                 "coherent mind and a practice that never stops improving.",
                 12.5, T["muted"], anchor="middle"))
    return h, s


def impact():
    """Improvement factor per workload, as a lollipop on a log axis.

    A linear "share of the original" bar cannot carry this data: the range runs
    from 3.3x to 161x, so the two best results collapse onto the minimum-width
    floor and the two weakest draw the longest bars -- the chart ends up
    ranking backwards. Every row shares the same left anchor (1x, the
    unchanged baseline), so distance travelled along a log axis is the win.
    Position carries the value here, not length from zero, which is what makes
    a log scale legitimate for this mark and not for a bar.
    """
    rows = [
        ("City-scale simulation run", "Unity raycasting, Manhattan",
         30 * 3600, 669, "30 h", "11 min", "faster"),
        ("PostGIS spatial query", "after index + memory retune",
         2000, 25, "2,000 ms", "25 ms", "faster"),
        ("Fleet data uploaded", "per vehicle, per day",
         100, 30, "100%", "30%", "less"),
        ("Agent context overhead", "per LLM call, tool schemas",
         10000, 300, "10k tok", "~300 tok", "less"),
        ("Web interaction latency", "INP, chat workspace",
         140, 40, "140 ms", "40 ms", "faster"),
        ("AUV steady-state error", "6-DoF controller, pool tests",
         100, 20, "baseline", "20%", "less"),
    ]
    rows.sort(key=lambda r: r[2] / r[3], reverse=True)

    ax, aw, amax = 262, 300, 200.0          # axis origin, span, right edge (x)
    span = math.log10(amax)

    def px(factor):
        return ax + aw * math.log10(max(factor, 1.0)) / span

    row_h, top = 52, 122
    h = top + row_h * (len(rows) - 1) + 46
    s = panel(h, "Improvement factor per workload, log scale, largest first")
    s.append(stripe(h))

    s.append(card_title("Numbers I moved"))
    s.append(txt(32, 66, "The same workload before and after my change. "
                "Farther right is a bigger win.", 12.5, T["muted"]))
    s.append(txt(32, 84, "Log scale — each gridline is 10× the one before it.",
                 10.5, T["faint"], mono=True))

    # axis: baseline at 1x plus decade gridlines, drawn under the marks
    grid_top, grid_bot = 106, top + row_h * (len(rows) - 1) + 22
    for factor in (1, 10, 100):
        gx = px(factor)
        first = factor == 1
        s.append(rect(gx, grid_top, 1, grid_bot - grid_top,
                      T["faint"] if first else dither(6, "d")))
        s.append(txt(gx, 100, f"{factor}×", 9.5, T["faint"], bold=first,
                     anchor="middle", mono=True))

    for i, (name, ctx, before, after, bl, al, word) in enumerate(rows):
        y = top + row_h * i
        factor = before / after
        dot = px(factor)

        s.append(txt(32, y - 3, name, 12.5, T["text"], bold=True))
        s.append(txt(32, y + 13, ctx, 10, T["faint"], mono=True))

        # connector + terminal dot: the run is dithered, the head is solid
        s.append(rect(ax, y, max(dot - ax, 1), 4, dither(10)))
        s.append(rect(ax - 2, y - 2, 4, 8, T["border"]))
        s.append(rect(dot - 5, y - 5, 10, 14, T["accent"]))
        s.append(rect(dot - 5, y - 5, 10, 14, "none", stroke=T["panel"],
                      sw=2))

        label = f"{factor:.0f}×" if factor >= 10 else f"{factor:.1f}×"
        s.append(txt(dot + 14, y + 7, label, 15, T["accent_text"], bold=True,
                     mono=True))
        s.append(txt(dot + 18 + tw(label, 15, bold=True), y + 7, word, 10,
                     T["faint"], mono=True))
        s.append(txt(W - 32, y + 6, f"{bl} → {al}", 11, T["muted"],
                     mono=True, anchor="end"))

        if i < len(rows) - 1:
            s.append(dither_rule(32, y + 26, W - 64, level=4))
    return h, s


def project(role, title, meta, hook, badges, nodes, stats, label):
    h = 268
    s = panel(h, label)
    s.append(stripe(h))

    s.append(txt(32, 40, role.upper(), 10.5, T["accent_text"], bold=True,
                 mono=True, spacing="1.6"))
    s.append(txt(32, 66, title.upper(), 16, T["text"], bold=True, mono=True,
                 spacing="0.8"))
    s.append(txt(32, 88, meta, 10.5, T["faint"], mono=True))
    s.append(txt(32, 114, hook, 12.5, T["muted"]))

    x = W - 32
    for text_, filled in reversed(badges):
        body, w = chip(0, 0, text_, size=10.5, h=21,
                       fill=T["accent"] if filled else T["bg"],
                       colour="#ffffff" if filled else T["muted"],
                       border=T["accent"] if filled else T["border"])
        x -= w
        s.append(f'<g transform="translate({x:.1f},51)">{body}</g>')
        x -= 7

    s.extend(flow(166, nodes))
    s.append(dither_ramp(28, 204, W - 56, steps=4, step_h=2, top=8))
    s.extend(tiles(238, stats))
    return h, s


def bonsai():
    """Custom card: v2 closes a loop through an off-vehicle server, so the
    plain left-to-right pipeline the other two cards use does not fit."""
    h = 324
    s = panel(h, "Bonsai Robotics on-vehicle data curation pipeline, v2")
    s.append(stripe(h))

    s.append(txt(32, 40, "BONSAI ROBOTICS · MACHINE LEARNING ENGINEERING "
                "INTERN", 10.5, T["accent_text"], bold=True, mono=True,
                spacing="1.6"))
    s.append(txt(32, 66, "ON-VEHICLE DATA CURATION PIPELINE", 16, T["text"],
                 bold=True, mono=True, spacing="0.8"))
    s.append(txt(32, 88, "C++ / ROS 2 · private repo · merged to main, "
                "running on every vehicle", 10.5, T["faint"], mono=True))
    s.append(txt(32, 114, "A fleet records far more than anyone can upload, so "
                "the vehicle itself decides what is worth sending home.", 12.5,
                T["muted"]))

    x = W - 32
    for label, filled in reversed([("private", False), ("v2", False),
                                   ("C++ / ROS 2", True)]):
        body, w = chip(0, 0, label, size=10.5, h=21,
                       fill=T["accent"] if filled else T["bg"],
                       colour="#ffffff" if filled else T["muted"],
                       border=T["accent"] if filled else T["border"])
        x -= w
        s.append(f'<g transform="translate({x:.1f},51)">{body}</g>')
        x -= 7

    nodes = [("sensor stream", "MCAP recordings"),
             ("frame embeddings", "on-vehicle encoder"),
             ("window score", "distance to vectors"),
             ("upload gate", "race-free finalize"),
             ("cloud", "top windows only")]
    flow_cy = 220
    placed = layout_flow(nodes)
    s.extend(flow(flow_cy, nodes))

    # The off-vehicle half: a periodic pass over everything uploaded so far
    # refreshes the characteristic vectors each vehicle scores against.
    score_x, score_w = placed[2]
    cloud_x, cloud_w = placed[4]
    srv_cy = 151
    s.append(node_box(score_x, srv_cy, cloud_x + cloud_w - score_x,
                      "remote fleet server",
                      "periodic pass over the full dataset", bh=42,
                      dashed=True))
    s.append(txt(score_x - 12, srv_cy + 4, "off-vehicle", 9.5, T["faint"],
                 anchor="end", mono=True))

    s.append(varrow(score_x + score_w / 2, srv_cy + 21, flow_cy - 23,
                    "refreshed characteristic vectors"))
    s.append(varrow(cloud_x + cloud_w / 2, flow_cy - 23, srv_cy + 21,
                    "uploaded windows"))

    s.append(dither_ramp(28, 260, W - 56, steps=4, step_h=2, top=8))
    s.extend(tiles(294, [
        ("-70%", "upload volume"), ("8×", "usable score spread"),
        ("<3%", "latency for a distilled VLM"),
        ("287k", "frames embedded on Ray")]))
    return h, s


def langalpha():
    return project(
        "Ginlix AI · Full-Stack Software Engineer",
        "LangAlpha — Claude Code for financial markets",
        "Ginlix AI · Python · LangGraph · Postgres · Redis · full-stack "
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


def sunlight():
    return project(
        "Cornell Ezra Systems · Simulation Infrastructure Lead",
        "SunlightCity — 7.89B measurements in 11 minutes",
        "Cornell Ezra Systems · Unity · Kubernetes · PostGIS · "
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


# Each group is (short label, [tools first, then the concepts they go with]).
STACK_GROUPS = [
    ("Languages", [
        "Python", "C++", "Java", "Go", "Kotlin", "C#", "TypeScript",
        "JavaScript", "SQL", "Bash",
    ]),
    ("ML & Perception", [
        "PyTorch", "NumPy", "Pandas", "OpenCV", "YOLOv7", "CLIP", "SigLIP2",
        "TIPSv2", "BEV perception", "knowledge distillation",
        "vision-language models", "embedding pipelines", "benchmark design",
        "adaptive thresholding",
    ]),
    ("Agents & LLM systems", [
        "LangGraph", "LangChain", "MCP", "FastMCP", "RAG",
        "programmatic tool calling", "subagent orchestration",
        "context engineering", "memory compaction", "sandboxed execution",
        "SSE streaming", "tool routing",
    ]),
    ("Robotics & Control", [
        "ROS 2", "MCAP", "6-DoF control", "system identification",
        "controller tuning", "state machines", "sensor fusion",
        "LiDAR + camera", "real-time on-vehicle", "field-data iteration",
    ]),
    ("Backend & Web", [
        "Spring Boot", "FastAPI", "Node.js", "React", "TanStack Query",
        "Jetpack Compose", "Room", "Retrofit / OkHttp", "REST APIs",
        "WebSocket", "session auth", "stale-while-revalidate",
    ]),
    ("Data & Storage", [
        "PostgreSQL", "PostGIS", "Redis", "Elasticsearch", "SQLite",
        "sharding", "spatial indexing", "query tuning", "bulk ingest",
        "schema migration", "caching strategy",
    ]),
    ("Infrastructure & Scale", [
        "Docker", "Kubernetes", "AWS (RDS · ECR · App Runner)",
        "Ray / Anyscale", "Unity headless", "IL2CPP", "MapReduce",
        "autoscaling", "capacity planning", "CI/CD", "GitHub Actions",
        "Linux",
    ]),
    ("Foundations", [
        "Machine Learning", "Algorithms & Data Structures", "Databases",
        "Computer Organization", "Cryptography", "Probability",
        "Linear Algebra", "Distributed Systems",
    ]),
]


def wrap_text(text, max_w, size, bold=False, mono=False):
    """Greedy word-wrap to a pixel width."""
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and tw(trial, size, bold, mono) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def card_title(title, y=44):
    """The heading a markdown `##` used to carry, set in the card instead."""
    return txt(32, y, title.upper(), 15, T["text"], bold=True, mono=True,
               spacing="1.6")


def wrap_tags(items, x0, x_max, size, pad, gap):
    """Greedy-wrap tag pills into lines that fit the available width."""
    lines: list[list[tuple[str, float]]] = [[]]
    x = x0
    for item in items:
        w = tw(item, size, bold=True) + pad * 2
        if lines[-1] and x + w > x_max:
            lines.append([])
            x = x0
        lines[-1].append((item, w))
        x += w + gap
    return lines


def stack():
    size, pad, gap, pill_h, line_h = 10.5, 9, 6, 23, 29
    tag_x, tag_max = 230, W - 30

    laid = [(name, wrap_tags(items, tag_x, tag_max, size, pad, gap))
            for name, items in STACK_GROUPS]

    top = 84
    heights = [max(len(lines) * line_h, line_h) + 12 for _, lines in laid]
    h = top + sum(heights) + 6

    s = panel(h, "Technical stack, grouped by area")
    s.append(stripe(h))
    s.append(card_title("Stack"))
    s.append(txt(32, 66, "Tools I build with, and the ideas they go with — "
                "grouped by where I actually use them.", 12.5, T["muted"]))

    y = top
    for i, ((name, lines), block) in enumerate(zip(laid, heights)):
        if i:
            s.append(dither_rule(32, y - 8, W - 64, level=4))
        s.append(txt(32, y + 16, f"{i + 1:02d}", 10, T["accent_text"],
                     bold=True, mono=True))
        s.append(txt(56, y + 16, name, 12, T["text"], bold=True, mono=True))
        for row, line in enumerate(lines):
            ly = y + row * line_h
            x = tag_x
            for item, w in line:
                s.append(rect(x, ly, w, pill_h, T["bg"], rx=2,
                              stroke=T["border"]))
                s.append(txt(x + w / 2, ly + pill_h / 2 + size * 0.36, item,
                             size, T["muted"], anchor="middle", mono=True))
                x += w + gap
        y += block
    return h, s


# The two markdown tables, rebuilt as cards so the page stops switching
# between GitHub's table styling and this one. Repo links stay in the README
# underneath -- an image cannot carry a hyperlink.
SHELF = [
    ("GroceryManager", "Spring Boot · React · AWS App Runner",
     "Grocery list service with session auth, scaling horizontally without "
     "instance pinning.",
     "Search moved to Elasticsearch: ~400 ms faster and typo-tolerant, "
     "replacing SQL that degraded as the catalog grew."),
    ("Pixel Social", "React · Go · Elasticsearch · DALL·E 3",
     "Social platform for creating and sharing images and video.",
     "Go backend over an Elasticsearch index, with generative image creation "
     "inside the upload flow."),
    ("PaperChat", "Node.js · React · LangChain · MCP",
     "RAG and web-search chat over your own PDFs, with voice I/O.",
     "Retrieval and live search share one answer path, so citations stay "
     "attached to what was actually read."),
    ("MiniSpotify", "Kotlin · ExoPlayer · Jetpack Compose",
     "Android music client with offline-tolerant playback.",
     "Room + Kotlin Flows stale-while-revalidate cache: ~80% faster "
     "returning-user load. Backoff cut failed requests 25%."),
    ("Cornell AUV", "ROS 2 · YOLOv7 · control",
     "Autonomous underwater vehicle — perception, control, mission stack.",
     "Fit nonlinear models to 6-DoF pool-test data to find controller "
     "parameters hand-tuning missed: 80% less steady-state error."),
]


def shelf():
    col2, col3 = 292, 566
    w2, w3 = 250, W - col3 - 32
    rows = [(name, tech, wrap_text(what, w2, 10.5, mono=True),
             wrap_text(note, w3, 10.5, mono=True))
            for name, tech, what, note in SHELF]
    heights = [max(len(a), len(b)) * 15 + 30 for _, _, a, b in rows]

    top = 92
    h = top + sum(heights) + 8
    s = panel(h, "Other projects worth a look")
    s.append(stripe(h))
    s.append(card_title("Also on the shelf"))
    s.append(txt(32, 66, "Smaller builds, each one solving a problem the "
                "obvious approach could not.", 12.5, T["muted"]))

    y = top
    for i, ((name, tech, what, note), block) in enumerate(zip(rows, heights)):
        if i:
            s.append(dither_rule(32, y - 12, W - 64, level=4))
        s.append(txt(32, y + 4, name, 12.5, T["accent_text"], bold=True,
                     mono=True))
        s.append(txt(32, y + 20, tech, 9.5, T["faint"], mono=True))
        for j, line in enumerate(what):
            s.append(txt(col2, y + 4 + j * 15, line, 10.5, T["muted"],
                         mono=True))
        for j, line in enumerate(note):
            s.append(txt(col3, y + 4 + j * 15, line, 10.5, T["muted"],
                         mono=True))
        y += block
    return h, s


PRINCIPLES = [
    ("Tradeoffs, not perfect solutions",
     "Clarity over cleverness · observability over magic · iteration over "
     "over-design · user needs over technical ego."),
    ("The real world is the test",
     "A feature is cheap. A feature that holds under load, bad networks and "
     "odd inputs is the job."),
    ("Humans stay in the loop",
     "The user should understand why the system produced an answer, not just "
     "what the answer was."),
    ("Currently learning",
     "Reliable agent orchestration · AI infrastructure · robotics control "
     "powered by ML · system design at scale."),
]


def principles():
    col, wtext = 300, W - 300 - 32
    rows = [(label, wrap_text(body, wtext, 11, mono=True))
            for label, body in PRINCIPLES]
    heights = [max(len(b), 1) * 16 + 26 for _, b in rows]

    top = 92
    h = top + sum(heights) + 8
    s = panel(h, "How I think about the work")
    s.append(stripe(h))
    s.append(card_title("How I think about the work"))
    s.append(txt(32, 66, "The part of the job that does not show up in a "
                "stack list.", 12.5, T["muted"]))

    y = top
    for i, ((label, body), block) in enumerate(zip(rows, heights)):
        if i:
            s.append(dither_rule(32, y - 12, W - 64, level=4))
        s.append(txt(32, y + 4, f"{i + 1:02d}", 10, T["faint"], bold=True,
                     mono=True))
        s.append(txt(58, y + 4, label, 11.5, T["text"], bold=True, mono=True))
        for j, line in enumerate(body):
            s.append(txt(col, y + 4 + j * 16, line, 11, T["muted"], mono=True))
        y += block
    return h, s


CARDS = {
    "hero": hero,
    "impact": impact,
    "card-bonsai": bonsai,
    "card-langalpha": langalpha,
    "card-sunlightcity": sunlight,
    "stack": stack,
    "shelf": shelf,
    "principles": principles,
}


def write_card(out_dir, name, h, parts):
    parts.append(overlay(h))
    path = os.path.join(out_dir, f"{name}.svg")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(parts) + "\n</svg>\n")
    print(f"wrote {path} ({W}x{h})")


def main() -> None:
    out = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "profile")
    os.makedirs(out, exist_ok=True)
    for name, build in CARDS.items():
        h, parts = build()
        write_card(out, name, h, parts)


if __name__ == "__main__":
    main()
