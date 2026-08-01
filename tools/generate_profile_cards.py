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

import math
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
        # Eight-slot category order, validated adjacent-pair in this mode.
        "series": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
                   "#e87ba4", "#008300", "#4a3aa7", "#e34948"],
        "tint": 0.13,
    },
    "dark": {
        "panel": "#161b22", "inner": "#0d1117", "border": "#30363d",
        "text": "#e6edf3", "muted": "#9198a1", "faint": "#6e7681",
        "track": "#30363d", "chip": "#21262d", "rule": "#30363d",
        "cyan": "#1596b0", "amber": "#c98500",
        "violet": "#9085e9", "rose": "#e66767",
        "series": ["#3987e5", "#d95926", "#199e70", "#c98500",
                   "#d55181", "#008300", "#9085e9", "#e66767"],
        "tint": 0.20,
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


def varrow(t, x, y1, y2, label=None):
    """Vertical connector, head at y2. Label sits to the right of the shaft."""
    down = y2 > y1
    head_base = y2 - 8 if down else y2 + 8
    out = (f'<path d="M{x:.1f} {y1} V{head_base:.1f}" stroke="{t["faint"]}" '
           f'stroke-width="1.5" fill="none"/>'
           f'<path d="M{x:.1f} {y2} l-4,{-8 if down else 8} h8 z" '
           f'fill="{t["faint"]}"/>')
    if label:
        out += txt(x + 9, (y1 + y2) / 2 + 3.5, label, 10, t["faint"])
    return out


def node_box(t, x, cy, w, top, bot, accent, bh=46, dashed=False):
    dash = ' stroke-dasharray="5 4"' if dashed else ""
    body = (f'<rect x="{x:.1f}" y="{cy - bh / 2:.1f}" width="{w:.1f}" '
            f'height="{bh}" rx="8" fill="{t["inner"]}" '
            f'stroke="{t["border"]}" stroke-width="1"{dash}/>')
    if not dashed:
        body += rect(x, cy - bh / 2, w, 2.5, accent, rx=1.2)
    body += txt(x + w / 2, cy - 2, top, 11.5, t["text"], bold=True,
                anchor="middle")
    body += txt(x + w / 2, cy + 14, bot, 10.5, t["muted"], anchor="middle")
    return body


def layout_flow(nodes, gap=24, pad=15):
    """Widths and x positions for a centred pipeline. Returns [(x, w), ...]."""
    widths = [max(tw(top, 11.5, bold=True), tw(bot, 10.5)) + pad * 2
              for top, bot in nodes]
    x = (W - (sum(widths) + gap * (len(nodes) - 1))) / 2
    placed = []
    for w in widths:
        placed.append((x, w))
        x += w + gap
    return placed


def flow(t, cy, nodes, accent, gap=24):
    """Centred pipeline of two-line boxes joined by arrows."""
    placed = layout_flow(nodes, gap=gap)
    out = []
    for i, ((x, w), (top, bot)) in enumerate(zip(placed, nodes)):
        out.append(node_box(t, x, cy, w, top, bot, accent))
        if i < len(nodes) - 1:
            out.append(arrow(t, x + w + 5, x + w + gap - 5, cy))
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
    # Deliberately spare: identity, the three disciplines, and the reason.
    # Numbers and project detail live in the sections below, not up here.
    h = 214
    cx = W / 2
    s = panel(t, h, "Zhu (Leo) Zhi - software, machine learning and "
                    "robotics engineer")
    s.append(stripe(t, h, t["cyan"]))

    s.append(txt(cx, 46, "CORNELL CS '28   ·   GPA 4.0 / 4.0", 10.5,
                 t["faint"], bold=True, anchor="middle", spacing="1.4"))
    s.append(txt(cx, 92, "Zhu (Leo) Zhi", 40, t["text"], bold=True,
                 anchor="middle"))

    roles = [("Software Engineer", "cyan"),
             ("Machine Learning Engineer", "amber"),
             ("Robotics Engineer", "rose")]
    widths = [tw(label, 12, bold=True) + 26 for label, _ in roles]
    x = cx - (sum(widths) + 10 * (len(roles) - 1)) / 2
    for (label, key), w in zip(roles, widths):
        body, _ = chip(t, x, 116, label, size=12, pad=13, h=24,
                       colour=t[key])
        s.append(body)
        x += w + 10

    s.append(txt(cx, 174, "However the technical landscape shifts, "
                 "engineering keeps returning to one origin:", 13,
                 t["muted"], anchor="middle"))
    s.append(txt(cx, 194, "making things that solve real problems — with a "
                 "coherent mind and a practice that never stops improving.",
                 13, t["muted"], anchor="middle"))
    return h, s


def impact(t):
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

    row_h, top = 52, 116
    h = top + row_h * (len(rows) - 1) + 46
    s = panel(t, h, "Improvement factor per workload, log scale, "
                    "largest first")
    s.append(stripe(t, h, t["cyan"]))

    s.append(txt(32, 42, "The same workload before and after my change. "
                "Farther right is a bigger win.", 12.5, t["muted"]))
    s.append(txt(32, 62, "Log scale — each gridline is 10× the one before "
                "it.", 11, t["faint"]))

    # axis: baseline at 1x plus decade gridlines, drawn under the marks
    grid_top, grid_bot = 96, top + row_h * (len(rows) - 1) + 22
    for factor in (1, 10, 100):
        gx = px(factor)
        first = factor == 1
        s.append(f'<path d="M{gx:.1f} {grid_top} V{grid_bot}" '
                 f'stroke="{t["rule"] if first else t["track"]}" '
                 f'stroke-width="1"{"" if first else " opacity=\"0.5\""}/>')
        s.append(txt(gx, 88, f"{factor}×", 10, t["faint"], bold=first,
                     anchor="middle"))

    for i, (name, ctx, before, after, bl, al, word) in enumerate(rows):
        y = top + row_h * i
        factor = before / after
        dot = px(factor)

        s.append(txt(32, y - 3, name, 13, t["text"], bold=True))
        s.append(txt(32, y + 13, ctx, 10.8, t["faint"]))

        # connector + terminal dot: 1 hue, 2 shades (dumbbell convention)
        s.append(f'<path d="M{ax} {y + 2} H{dot:.1f}" stroke="{t["cyan"]}" '
                 f'stroke-width="2.5" opacity="0.42" stroke-linecap="round"/>')
        s.append(f'<circle cx="{ax}" cy="{y + 2}" r="3.5" '
                 f'fill="{t["track"]}"/>')
        s.append(f'<circle cx="{dot:.1f}" cy="{y + 2}" r="6" '
                 f'fill="{t["cyan"]}" stroke="{t["panel"]}" '
                 f'stroke-width="2"/>')

        label = f"{factor:.0f}×" if factor >= 10 else f"{factor:.1f}×"
        s.append(txt(dot + 14, y + 7, label, 15, t["cyan"], bold=True))
        s.append(txt(dot + 16 + tw(label, 15, bold=True), y + 7, word, 10.5,
                     t["faint"]))
        s.append(txt(W - 32, y + 6, f"{bl} → {al}", 11.5, t["muted"],
                     mono=True, anchor="end"))

        if i < len(rows) - 1:
            s.append(f'<path d="M32 {y + 26} H{W - 32}" stroke="{t["rule"]}" '
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
    """Custom card: v2 closes a loop through an off-vehicle server, so the
    plain left-to-right pipeline the other two cards use does not fit."""
    h, accent = 306, t["cyan"]
    s = panel(t, h, "Bonsai Robotics on-vehicle data curation pipeline, v2")
    s.append(stripe(t, h, accent))

    s.append(txt(32, 44, "On-Vehicle Data Curation Pipeline", 19, accent,
                 bold=True))
    s.append(txt(32, 66, "Bonsai Robotics  ·  C++ / ROS 2  ·  private repo  ·  "
                "merged to main, running on every vehicle", 11.5, t["faint"],
                mono=True))
    s.append(txt(32, 92, "A fleet records far more than anyone can upload, so "
                "the vehicle itself decides what is worth sending home.", 13,
                t["text"]))

    x = W - 32
    for label, filled in reversed([("private", False), ("v2", False),
                                   ("C++ / ROS 2", True)]):
        body, w = chip(t, 0, 0, label, size=11, h=21,
                       fill=accent if filled else t["chip"],
                       colour=t["inner"] if filled else t["muted"])
        x -= w
        s.append(f'<g transform="translate({x:.1f},31)">{body}</g>')
        x -= 7

    nodes = [("sensor stream", "MCAP recordings"),
             ("frame embeddings", "on-vehicle encoder"),
             ("window score", "distance to vectors"),
             ("upload gate", "race-free finalize"),
             ("cloud", "top windows only")]
    flow_cy = 202
    placed = layout_flow(nodes)
    s.extend(flow(t, flow_cy, nodes, accent))

    # The off-vehicle half: a periodic pass over everything uploaded so far
    # refreshes the characteristic vectors each vehicle scores against.
    score_x, score_w = placed[2]
    cloud_x, cloud_w = placed[4]
    srv_x = score_x
    srv_w = cloud_x + cloud_w - score_x
    srv_cy = 133
    s.append(node_box(t, srv_x, srv_cy, srv_w, "remote fleet server",
                      "periodic pass over the full dataset", accent,
                      bh=42, dashed=True))
    s.append(txt(srv_x - 12, srv_cy + 4, "off-vehicle", 10, t["faint"],
                 anchor="end"))

    s.append(varrow(t, score_x + score_w / 2, srv_cy + 21, flow_cy - 23,
                    "refreshed characteristic vectors"))
    s.append(varrow(t, cloud_x + cloud_w / 2, flow_cy - 23, srv_cy + 21,
                    "uploaded windows"))

    s.append(f'<path d="M28 248 H{W - 28}" stroke="{t["rule"]}" '
             f'stroke-width="1"/>')
    s.extend(tiles(t, 274, [
        ("-70%", "upload volume"), ("8×", "usable score spread"),
        ("<3%", "latency for a distilled VLM"),
        ("287k", "frames embedded on Ray")], accent))
    return h, s


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


# Each group is (short label, [tools first, then the concepts they go with]).
# Colour comes from the theme's validated 8-slot order, by position; every
# group is also named in text, so identity never rests on colour alone.
STACK_GROUPS = [
    ("Languages", [
        "Python", "C++", "Java", "Go", "Kotlin", "C#", "TypeScript",
        "JavaScript", "SQL", "Bash",
    ]),
    ("ML & Perception", [
        "PyTorch", "NumPy", "Pandas", "OpenCV", "YOLOv7", "CLIP", "SigLIP2",
        "TIPSv2", "BEV perception", "knowledge distillation",
        "vision–language models", "embedding pipelines", "benchmark design",
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


def stack(t):
    size, pad, gap, pill_h, line_h = 11, 10, 6, 24, 30
    label_x, tag_x, tag_max = 32, 208, W - 30

    laid = [(name, wrap_tags(items, tag_x, tag_max, size, pad, gap))
            for name, items in STACK_GROUPS]

    top = 62
    heights = [max(len(lines) * line_h, line_h) + 12 for _, lines in laid]
    h = top + sum(heights) + 6

    s = panel(t, h, "Technical stack, grouped by area")
    s.append(stripe(t, h, t["violet"]))
    s.append(txt(32, 42, "Tools I build with, and the ideas they go with — "
                "grouped by where I actually use them.", 12.5, t["muted"]))

    y = top
    for i, ((name, lines), block) in enumerate(zip(laid, heights)):
        colour = t["series"][i % len(t["series"])]
        if i:
            s.append(f'<path d="M32 {y - 6} H{W - 32}" stroke="{t["rule"]}" '
                     f'stroke-width="1" opacity="0.5"/>')
        # Label in text ink, not the series colour -- several slots sit below
        # 3:1 on the light surface and turn to mush when used as type. The dot
        # and the pill tint carry the identity instead.
        s.append(f'<circle cx="36" cy="{y + 12}" r="4.5" fill="{colour}"/>')
        s.append(txt(48, y + 16, name, 12.5, t["text"], bold=True))
        for row, line in enumerate(lines):
            ly = y + row * line_h
            x = tag_x
            for item, w in line:
                s.append(rect(x, ly, w, pill_h, colour, rx=pill_h / 2,
                              opacity=t["tint"]))
                s.append(txt(x + w / 2, ly + pill_h / 2 + size * 0.36, item,
                             size, t["text"], bold=True, anchor="middle"))
                x += w + gap
        y += block
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
