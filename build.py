#!/usr/bin/env python3
"""Build the homepage and the COLM project page.

Content lives in content/:
  site.json          name, links, intro text
  publications.json  paper metadata (title, authors, venue, links)
  research.json      per paper: what the model knows, what it does, evidence
  experience.json    roles
  now.json           "Now" lines (not shown on the homepage since 2026-11; kept for reuse)
  news.json          dated news items
  projects.json      funded projects, each tied to a topic
Run:  python3 build.py      (standard library only)
"""
from __future__ import annotations

import hashlib
import html
import json
import math
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"


def load(name):
    return json.loads((CONTENT / name).read_text(encoding="utf-8"))


site = load("site.json")
papers = load("publications.json")
research = load("research.json")
experience = load("experience.json")
news = load("news.json")["items"]
projects = load("projects.json")["items"]
ME = site["featured_author"]

def css(prefix: str, name: str) -> str:
    """Stylesheet link with a content hash, so browsers never keep a stale copy after a deploy."""
    v = hashlib.md5((ROOT / "assets" / "css" / name).read_bytes()).hexdigest()[:8]
    return f'<link rel="stylesheet" href="{prefix}assets/css/{name}?v={v}">'


def fonts(prefix: str = "") -> str:
    return (f'<link rel="preload" href="{prefix}assets/fonts/pixelify-sans-latin-500-normal.woff2" as="font" type="font/woff2" crossorigin>'
            + css(prefix, "fonts.css"))


def h(value) -> str:
    return html.escape(str(value), quote=True)


def nb(text: str) -> str:
    """Escape, and keep hyphenated compounds (Label-Free) from breaking at the hyphen."""
    return re.sub(r"(\w+(?:-\w+)+)", r'<span class="nb">\1</span>', h(text))


def ext(url: str) -> str:
    return ' target="_blank" rel="noopener noreferrer"' if url.startswith(("http://", "https://")) else ""


def arxiv_id(p: dict):
    m = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", p.get("url", ""))
    return m.group(1) if m else None


def key_of(p: dict) -> str:
    """Stable id for a paper: its arXiv id, or a slug of the title."""
    return arxiv_id(p) or re.sub(r"[^a-z0-9]+", "-", p["title"].lower()).strip("-")[:48]


def year_of(p: dict) -> int:
    if p.get("year"):
        return int(p["year"])
    m = re.search(r"(20\d{2})\b", p["venue"])
    if m:
        return int(m.group(1))
    a = arxiv_id(p)
    return 2000 + int(a[:2]) if a else 0


def is_preprint(p: dict) -> bool:
    return p["venue"].lower() == "preprint"


def order(ps):
    """Published first, then preprints; newest first within each."""
    return sorted(ps, key=lambda p: (-year_of(p), -float(arxiv_id(p) or p.get("sort_key", 0))))


# Sprites ----------------------------------------------------------------------------
# 16x16 pixel art, one character per pixel. '.' is transparent.
ME_SPRITE = [
    "................",
    ".....KKKKKK.....",
    "...KKKKKKKKKK...",
    "..KKKKKKKKKKKK..",
    "..KKKKKKKKKKKKK.",
    "..KKKKKKKKSKKKK.",
    "..KKSSKKKSSSKKK.",
    "..KSSSSSSSSSSSK.",
    "..SSSESSSSESSSS.",
    "..SSSESSSSESSSs.",
    "..SSSSSSSSSSSSs.",
    "...SSSSSMMSSSs..",
    "....sSSSSSSSs...",
    "...WWWWssWWWW...",
    "..WWWWWWWWWWWW..",
    ".WWWwWWWWWWwWWW.",
]
ME_COLORS = {"K": "#1c1c22", "S": "#f1d9c6", "s": "#ddbfa8", "E": "#1c1c22", "M": "#b98a7a",
             "W": "#2a2a31", "w": "#3d3d46"}

LLM = [  # the robot at 16px, for small placements; same shape as LLM_HI
    ".......AA.......",
    ".......OO.......",
    "..OOOOOOOOOOOO..",
    ".OLLLLLLLLLLLLO.",
    ".OLddddddddddLO.",
    "EOLdZZddddZZdLOE",
    "EOLdZZddddZZdLOE",
    "EOLddddddddddLOE",
    "EOLdddZZZZdddLOE",
    ".OLLLLLLLLLLLLO.",
    ".OOOOOOOOOOOOOO.",
    "..OLLLLLLLLLLO..",
    "..OLLLAAAALLLO..",
    "..OLLLLLLLLLLO..",
    "..OOOOOOOOOOOO..",
]
LLM_COLORS = {"O": "#1c1c22", "L": "#ececf0", "d": "#24242b", "Z": "#3fe0a6", "A": "#13a374", "E": "#13a374"}
LLM_CLS = {"O": "ink", "L": "shell", "d": "screen", "Z": "eye", "A": "acc", "E": "acc"}


def _rr(x, y, x0, y0, x1, y1, r):
    """Is pixel (x, y) inside the rounded rectangle [x0..x1]x[y0..y1] with corner radius r?"""
    if not (x0 <= x <= x1 and y0 <= y <= y1):
        return False
    cx = min(max(x, x0 + r), x1 - r)
    cy = min(max(y, y0 + r), y1 - r)
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r + .5


def _llm_hi():
    """The same robot at twice the resolution (32x32), so its pixels match the rest of the scene."""
    W = H = 32
    g = [["."] * W for _ in range(H)]
    shapes = [  # (rounded rect, radius, fill), outlined in ink; later shapes paint over earlier ones
        ((5, 23, 26, 31), 1, "L"),   # torso
        ((3, 6, 28, 23), 2, "L"),    # head
    ]
    for (x0, y0, x1, y1), r, fill in shapes:
        for y in range(H):
            for x in range(W):
                if _rr(x, y, x0, y0, x1, y1, r):
                    edge = any(not _rr(x + dx, y + dy, x0, y0, x1, y1, r) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                    g[y][x] = "O" if edge else fill
    for y in range(H):
        for x in range(W):
            if _rr(x, y, 6, 9, 25, 20, 1):
                g[y][x] = "d"                                    # visor
            if _rr(x, y, 9, 12, 12, 16, 1) or _rr(x, y, 19, 12, 22, 16, 1):
                g[y][x] = "Z"                                    # eyes
            if (_rr(x, y, 0, 11, 2, 18, 0) or _rr(x, y, 29, 11, 31, 18, 0)):
                g[y][x] = "E"                                    # ear bolts
            if _rr(x, y, 14, 0, 17, 3, 1.5):
                g[y][x] = "A"                                    # antenna tip
            if 15 <= x <= 16 and 4 <= y <= 5:
                g[y][x] = "O"                                    # antenna stem
            if 13 <= x <= 18 and 26 <= y <= 27:
                g[y][x] = "A"                                    # chest light
    for x, y in ((13, 18), (14, 19), (15, 19), (16, 19), (17, 19), (18, 18)):
        g[y][x] = "Z"                                            # smile
    return ["".join(r) for r in g]


LLM_HI = _llm_hi()

GLYPHS = {"L": ["X..", "X..", "X..", "X..", "XXX"],
          "M": ["X...X", "XX.XX", "X.X.X", "X...X", "X...X"]}


def sprite(rows, colors, cls="", label=""):
    rects = "".join(
        f'<rect x="{x}" y="{y}" width="1" height="1" fill="{colors[c]}"/>'
        for y, row in enumerate(rows) for x, c in enumerate(row) if c != ".")
    aria = f'role="img" aria-label="{h(label)}"' if label else 'aria-hidden="true"'
    return f'<svg class="sprite {cls}" viewBox="0 0 {len(rows[0])} {len(rows)}" shape-rendering="crispEdges" {aria}>{rects}</svg>'


def llm(cls="llm"):
    return sprite(LLM, LLM_COLORS, cls)


def llm_rects(ox, oy, k=1, rows=None):
    return "".join(px_rect(ox + x * k, oy + y * k, k, k, LLM_CLS[c])
                   for y, row in enumerate(rows or LLM) for x, c in enumerate(row) if c != ".")


def typing(x, y, k=1):
    """A chat bubble with three typing dots, tail pointing down-left."""
    w, hh = 13 * k, 7 * k
    out = [px_rect(x + k, y, w - 2 * k, k, "ink"), px_rect(x + k, y + hh - k, w - 2 * k, k, "ink"),
           px_rect(x, y + k, k, hh - 2 * k, "ink"), px_rect(x + w - k, y + k, k, hh - 2 * k, "ink"),
           px_rect(x + k, y + k, w - 2 * k, hh - 2 * k, "white"),
           px_rect(x + k, y + hh, k, k, "ink"), px_rect(x, y + hh + k, k, k, "ink")]
    for i in range(3):
        out.append(px_rect(x + (3 + i * 3) * k, y + 3 * k, k, k, "dot", f"--d:{i * .25:.2f}s"))
    return "".join(out)


# Homepage ---------------------------------------------------------------------------
def authors(p: dict) -> str:
    return ", ".join(f'<b>{h(a)}</b>' if a == ME else h(a) for a in p["authors"])


def short_venue(p: dict) -> str:
    v = p.get("venue_short") or re.sub(r"\s*20\d{2}$", "", p["venue"]).strip()
    if v.lower().startswith("findings of "):
        v = v[12:] + " Findings"
    return v


SPOTLIGHT = [  # a stage light on a stand (X) throwing its beam (A) onto the badge to its right
    "............AA", "..........AAAA", ".XXX....AAAAAA", "XXXXXAAAAAAAAA", "XXXXXAAAAAAAAA",
    ".XXX....AAAAAA", "..X.......AAAA", "..X.........AA", ".XXX.........."]


def award_line(p: dict) -> str:
    a = p.get("award")
    if not a:
        return ""
    ico = sprite(SPOTLIGHT, {"X": "#1c1c22", "A": "#b9e8d5"}, "aw-ico")
    return (f'<p class="award">{ico}<span class="ak">{h(a["label"])}</span>'
            f'<span class="at">{h(a["text"])}</span></p>')


def title_html(p: dict) -> str:
    return f'<a href="{h(p["url"])}"{ext(p["url"])}>{nb(p["title"])}</a>' if p.get("url") else nb(p["title"])


def pub_row(p: dict) -> str:
    k = key_of(p)
    aid = arxiv_id(p)
    r = research.get(k, {})
    links = [f'<a href="{h(p["url"])}"{ext(p["url"])}>{p.get("url_label") or ("arXiv" if aid else "Paper")}</a>'] if p.get("url") else []
    if aid:
        links.append(f'<a href="https://arxiv.org/pdf/{aid}"{ext("https://")}>PDF</a>')
    for i in p.get("links", []):
        if i["label"].lower() == "project":
            links.append(f'<a href="{h(i["url"])}">Project</a>')
        elif i["url"].rstrip("/") != p.get("url", "").rstrip("/") and i["label"].lower() not in ("paper",):
            links.append(f'<a href="{h(i["url"])}"{ext(i["url"])}>{h(i["label"])}</a>')
    tldr_btn = (f'<button type="button" class="tldr" aria-expanded="false" aria-controls="t-{h(k)}">TL;DR</button>'
                if r.get("line") else "")
    tldr = f'<p class="tldr-text" id="t-{h(k)}" hidden>{h(r["line"])}</p>' if r.get("line") else ""
    note = f'<p class="note">{h(p["note"])}</p>' if p.get("note") else ""
    kind = "preprint" if is_preprint(p) else "published"
    return f"""
        <li class="pub" id="p-{h(k)}" data-kind="{kind}" data-topic="{topic_of(p)}">
          <span class="tag {kind}">{"<br>".join(h(x) for x in short_venue(p).split(chr(10)))}</span>
          <div>
            <h3>{title_html(p)}</h3>
            <p class="who">{authors(p)}</p>
            {award_line(p)}{note}
            <div class="links">{''.join(links)}{tldr_btn}</div>
            {tldr}
          </div>
        </li>"""


def publications(ps) -> str:
    years = sorted({year_of(p) for p in ps}, reverse=True)
    groups = []
    for y in years:
        rows = "".join(pub_row(p) for p in ps if year_of(p) == y)
        groups.append(f'<section class="year" data-year="{y}"><h3 class="y">{y}</h3><ol>{rows}</ol></section>')
    return "".join(groups)


topics_data = load("topics.json")
TOPICS = topics_data["topics"]


def topic_of(p):
    return p.get("research_area", "internals")


# Scenes ------------------------------------------------------------------------------
# Both scenes share an 80x40 pixel canvas and the same robot, seen two ways.
def px_rect(x, y, w=1, h_=1, cls="", style=""):
    st = f' style="{style}"' if style else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h_}" class="{cls}"{st}/>'


def lens_ring(cx, cy, r):
    out = []
    for y in range(-r - 1, r + 2):
        for x in range(-r - 1, r + 2):
            d = (x * x + y * y) ** .5
            if r - .5 <= d < r + .5:
                out.append(px_rect(cx + x, cy + y, 1, 1, "ink"))
    for i in range(1, 6):
        out.append(px_rect(cx + r - 1 + i, cy + r - 1 + i, 2, 2, "ink"))
    return "".join(out)


def ring(cx, cy, r, cls="ink"):
    return "".join(px_rect(cx + x, cy + y, 1, 1, cls)
                   for y in range(-r - 1, r + 2) for x in range(-r - 1, r + 2)
                   if r - .5 <= (x * x + y * y) ** .5 < r + .5)


def scene_internals() -> str:
    ox, oy = 8, 5                             # the bot, drawn at full resolution, on the left
    out = [llm_rects(ox, oy, 1, LLM_HI), typing(ox + 22, oy - 5)]
    # a magnified callout of what is inside its head
    cx, cy, r = 60, 20, 13
    out.append(f'<circle cx="{cx + .5}" cy="{cy + .5}" r="{r}" class="glass-fill"/>')
    xs = [cx - 7, cx - 3, cx + 1, cx + 5]
    for li, y in enumerate((cy + 6, cy, cy - 6)):
        for ni, x in enumerate(xs):
            out.append(px_rect(x, y, 2, 2, "node", f"--d:{li * .45 + ni * .05:.2f}s"))
    for y in (cy + 3, cy - 3):
        for x in xs:
            out.append(px_rect(x + .5, y, 1, 1, "wire"))
    out.append(ring(cx, cy, r))
    # dotted leader lines from the head to the callout
    hx0, hy0, hx1, hy1 = ox + 32, oy + 11, ox + 32, oy + 19
    for t in range(1, 9):
        out.append(px_rect(round(hx0 + (cx - 12 - hx0) * t / 9), round(hy0 + (cy - 8 - hy0) * t / 9), 1, 1, "wire lead"))
        out.append(px_rect(round(hx1 + (cx - 12 - hx1) * t / 9), round(hy1 + (cy + 8 - hy1) * t / 9), 1, 1, "wire lead"))
    return "".join(out)


PEOPLE = [  # 8x9 busts; h = hair, s = skin, t = top
    ["..hhhh..", ".hhhhhh.", ".hssssh.", ".sksskh.", ".ssssss.", "..ssss..", ".tttttt.", "tttttttt", "tttttttt"],
    [".hhhhhh.", "hhhhhhhh", "hhssssh.", "hskssks.", "hssssss.", "h.ssss..", ".tttttt.", "tttttttt", "tttttttt"],
    ["...hh...", "..hhhh..", ".hssssh.", ".sksskh.", ".ssssss.", "..ssss..", ".tttttt.", "tttttttt", "tttttttt"],
    ["hhhhhhhh", ".hhhhhh.", ".ssssss.", ".skssks.", ".ssssss.", "..ssss..", ".tttttt.", "tttttttt", "tttttttt"],
]
TOPS = ["t1", "t2", "t3", "acc", "t2", "t1"]


def scene_simulation() -> str:
    out = []
    # the robot, small, at the centre bottom
    out.append(llm_rects(32, 25))             # same robot as Internals, at the people's pixel size
    # six people in an arc, each voiced by the robot
    seats = [(6, 22), (16, 10), (30, 2), (42, 2), (56, 10), (66, 22)]
    for i, (sx, sy) in enumerate(seats):
        face = PEOPLE[i % len(PEOPLE)]
        g = [f'<g class="person" style="--d:{i * .12:.2f}s">']
        for y, row in enumerate(face):
            for x, c in enumerate(row):
                if c == ".":
                    continue
                cls = {"h": "hair" if i % 3 else "hair2", "s": "skin", "k": "ink", "t": TOPS[i]}[c]
                g.append(px_rect(sx + x, sy + y, 1, 1, cls))
        # a speech pip that blinks in turn
        g.append(px_rect(sx + 9, sy - 1, 3, 2, "pip", f"--d:{.8 + i * .35:.2f}s"))
        g.append("</g>")
        out.append("".join(g))
        # dotted line from the antenna up to each person
        ax, ay = 40, 24
        tx, ty = sx + 4, sy + 10
        for t in range(1, 6):
            fx = ax + (tx - ax) * t / 6
            fy = ay + (ty - ay) * t / 6
            out.append(px_rect(round(fx), round(fy), 1, 1, "wire", f"--d:{.6 + t * .05:.2f}s"))
    out.append(typing(42, 15))              # drawn last, on top of the dotted lines
    return "".join(out)


FIELD_ROWS = [  # crop parcels seen from above; letters pick a fill
    "aaabbbccaab", "aaabbbccaab", "ddaabbbccdd", "ddaabbbccdd", "cccddaaabbb", "cccddaaabbb",
]
FIELD_CLS = {"a": "t2", "b": "acc", "c": "t1", "d": "node"}


def scene_satellite() -> str:
    out = [llm_rects(4, 15)]                  # the same robot, small, reading the map
    # a satellite in orbit, top left: body + two panels
    sx, sy = 30, 2
    out.append(px_rect(sx, sy + 1, 4, 3, "ink"))
    for dx in (-6, 5):
        out.append(px_rect(sx + dx, sy + 1, 5, 3, "t3"))
        out.append(px_rect(sx + dx + 2, sy + 1, 1, 3, "wire"))
    # its scan beam down to the fields
    for t in range(1, 9):
        out.append(px_rect(sx + 1 + t * 2, sy + 4 + t * 2, 2, 1, "beam", f"--d:{t * .12:.2f}s"))
    # a patchwork of fields, bottom right, 3x3 px per parcel
    fx, fy = 44, 20
    for y, row in enumerate(FIELD_ROWS):
        for x, c in enumerate(row):
            out.append(px_rect(fx + x * 3, fy + y * 3, 3, 3, FIELD_CLS[c] + " field", f"--d:{(x + y) * .08:.2f}s"))
    out.append(px_rect(fx - 1, fy - 1, len(FIELD_ROWS[0]) * 3 + 2, 1, "ink"))
    out.append(px_rect(fx - 1, fy + len(FIELD_ROWS) * 3, len(FIELD_ROWS[0]) * 3 + 2, 1, "ink"))
    out.append(px_rect(fx - 1, fy - 1, 1, len(FIELD_ROWS) * 3 + 2, "ink"))
    out.append(px_rect(fx + len(FIELD_ROWS[0]) * 3, fy - 1, 1, len(FIELD_ROWS) * 3 + 2, "ink"))
    # dotted line from the robot to the map
    for t in range(1, 7):
        out.append(px_rect(26 + t * 3, 30, 1, 1, "wire lead"))
    out.append(typing(16, 10))
    return "".join(out)


TOPIC_ICONS = {  # 9x9 pixel marks, one per research direction; X = ink, A = accent. Shown on the hero keywords and signposts.
    "internals": [".....A...", "....XXX..", ".XXXXXXX.", ".X.....X.", "XX.A.A.XX", ".X.....X.", ".X.XXX.X.", ".XXXXXXX.", "........."],
    "simulation": ["XXXXX....", "X...X....", "XXXXX....", ".X.......", "....AAAAA", "....A...A", "....AAAAA", ".......A.", "........."],
    "satellite": ["....X....", "...XXX...", "XX.XXX.XX", "XXXXXXXXX", "XX.XXX.XX", "...XXX...", "....X....", "...A.A...", "..A...A.."],
}


def ticon(k: str) -> str:
    return sprite(TOPIC_ICONS[k], {"X": "#1c1c22", "A": "#13a374"}, "ticon") if k in TOPIC_ICONS else ""


def tname(t, upper=False):
    """Topic name; 'lines' in topics.json sets where a long name breaks."""
    parts = t.get("lines") or [t["name"]]
    return "<br>".join(f'<span class="nw">{h(x.upper() if upper else x)}</span>' for x in parts)


def project_count(k):
    return sum(pr.get("topic") == k for pr in projects)


# Now, news, projects -----------------------------------------------------------------
def month_label(d):
    y, m = d.split("-")
    return f'{["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"][int(m) - 1]} {y}'


NEWS_ICONS = {  # 8x8 pixel icons per news kind; X = ink, A = accent
    "accepted": ["........", "......AA", ".....AA.", "A...AA..", "AA.AA...", ".AAA....", "..A.....", "........"],
    "preprint": ["XXXXX...", "X...XX..", "X.XXXXX.", "X.....X.", "X.XXX.X.", "X.....X.", "X.XXX.X.", "XXXXXXX."],
    "talk":     [".XXXXXX.", "X......X", "X.A.A.AX", "X......X", ".XXXXXX.", "...X....", "..X.....", "........"],
    "visit":    ["...XX...", "..XAAX..", "..XAAX..", "...XX...", "...XX...", "..X..X..", ".X....X.", "XXXXXXXX"],
}
NEWS_LABEL = {"accepted": "ACCEPTED", "preprint": "PREPRINT", "talk": "TALK", "visit": "VISIT"}


def news_block(today: str, prefix: str = "") -> str:
    def row(n):
        kind = n.get("kind", "talk")
        soon = n["date"] > today
        title = h(n.get("title", ""))
        if n.get("url") and title:
            title = f'<a href="{h(rel(n["url"], prefix))}"{ext(n["url"])}>{title}</a>'
        badge = f'<span class="nk {kind}{" soon" if soon else ""}">{"SOON" if soon else NEWS_LABEL.get(kind, kind.upper())}</span>'
        ico = sprite(NEWS_ICONS.get(kind, NEWS_ICONS["talk"]), {"X": "#1c1c22", "A": "#13a374"}, "nico")
        return (f'<li class="n-{kind}"><span class="nicon">{ico}</span><div>'
                f'<p class="nmeta"><time datetime="{h(n["date"])}">{month_label(n["date"])}</time>{badge}</p>'
                f'<p class="nhead">{h(n["head"])}</p>'
                + (f'<p class="ntitle">{title}</p>' if title else "") + '</div></li>')
    rows = "".join(row(n) for n in news)
    return f"""
  <section class="side" aria-labelledby="news-h">
    <h2 id="news-h"><span>NEWS</span></h2>
    <div class="news px"><ol tabindex="0" aria-label="News, newest first">{rows}</ol></div>
  </section>"""


def projects_block() -> str:
    def card(pr):
        t = TOPICS.get(pr.get("topic"), {"name": ""})
        title = f'<a href="projects/{h(pr["slug"])}/">{h(pr["title"])}</a>'
        return f"""
      <li class="proj">
        <span class="tag">{tname(t, upper=True)}</span>
        <div>
          <h3>{title}</h3>
          <p class="who">{h(pr["partner"])} · {h(pr["period"])}</p>
          <p class="line">{h(pr["line"])}</p>
          <div class="links"><a href="projects/{h(pr["slug"])}/">Details</a></div>
        </div>
      </li>"""
    return f"""
  <section aria-labelledby="proj-h">
    <h2 id="proj-h"><span>PROJECTS</span><small class="count">{len(projects)} FUNDED</small></h2>
    <ol class="projs px">{"".join(card(pr) for pr in projects)}</ol>
  </section>"""


EXP_ICONS = {  # 10x10 pixel icons for the save slots; X = ink. Add one per organization (fallback: robot).
    "OTDA": ["....XX....", "...X..X...", "......X...", ".....X....", "....XX....", "...X..X...", "..X....X..", ".X......X.", "XXXXXXXXXX", ".........."],
    "KAIST & IBS": ["XX......XX", "XX......XX", "..X....X..", "...X..X...", "....XX....", "....XX....", "...X..X...", "..X....X..", "XX......XX", "XX......XX"],
    "NSUSLAB": ["XXXXXXXXXX", "X........X", "X........X", "X.X..X..XX", "X........X", "X........X", "XXXXXXXXXX", "XX........", "X.........", ".........."],
}
NOW_YEAR = 2026


def exp_icon(org):
    rows = EXP_ICONS.get(org)
    return sprite(rows, {"X": "#1c1c22"}, "ico") if rows else sprite(LLM, LLM_COLORS, "ico")


def exp_tag(i):
    return "FOUNDER" if i["role"].lower() == "founder" else i["track"].upper()


def experience_block() -> str:
    """A timeline strip for the overview, then one save slot per role. The two are linked."""
    rows = sorted(experience, key=lambda i: (i["end_year"] is not None, -(i["end_year"] or 9999), -i["start_year"]))
    y0 = min(i["start_year"] for i in rows)
    span = NOW_YEAR - y0 + 1
    yrs = lambda i: h(i["date"].replace("–present", "–NOW"))

    def blk(k, i):
        e = i["end_year"] or NOW_YEAR
        left, w = (i["start_year"] - y0) / span * 100, (e - i["start_year"] + 1) / span * 100
        cls = "cur" if i["end_year"] is None else i["track"]
        return (f'<a class="blk {cls}" href="#x-{k}" data-k="{k}" style="left:{left:.2f}%;width:calc({w:.2f}% - 4px)" '
                f'title="{h(i["organization"])} · {yrs(i)}">{h(i["organization"])}</a>')

    tracks = [t for t in ("research", "industry") if any(i["track"] == t for i in rows)]
    lanes = "".join(
        f'<div class="lane"><span class="ln">{t.upper()}</span><div class="lane-track" style="--span:{span}">'
        + "".join(blk(k, i) for k, i in enumerate(rows) if i["track"] == t) + "</div></div>" for t in tracks)
    years = "".join(f'<span>{y if y < NOW_YEAR else "NOW"}</span>' for y in range(y0, NOW_YEAR + 1))
    slots = "".join(f"""
      <article class="slot px{' cur' if i['end_year'] is None else ''}" id="x-{k}" data-k="{k}">
        <header><span>SLOT {k + 1:02d}</span><span>{yrs(i)}</span></header>
        <div class="slot-body"><span class="slot-ico">{exp_icon(i['organization'])}</span>
          <div><h3>{h(i['organization'])}</h3><p class="r">{h(i['role'])}</p></div></div>
        <p class="q">{h(i['detail'])}</p>
        <footer><span class="chip">{exp_tag(i)}</span>{'<span class="cont"><i></i>CONTINUE</span>' if i['end_year'] is None else '<span>CLEAR</span>'}</footer>
      </article>""" for k, i in enumerate(rows))
    return f"""
    <div class="tl px" aria-label="Timeline">
      <div class="tl-years"><span></span><div class="tl-head" style="--span:{span}">{years}<span class="me-now">{sprite(ME_SPRITE, ME_COLORS, "ico")}</span></div></div>
      {lanes}
    </div>
    <div class="slots">{slots}
    </div>"""


SCAN = r"""
<script>
(() => {
  document.querySelector('.theme')?.addEventListener('click', () => {
    const d = document.documentElement, t = d.dataset.theme === 'dark' ? 'light' : 'dark';
    d.dataset.theme = t; try { localStorage.setItem('theme', t); } catch (_) {}
  });
  // The grid is a map: cells light up where the pointer passes, like pixels being classified
  if (matchMedia('(prefers-reduced-motion: reduce)').matches || !matchMedia('(hover: hover)').matches) return;
  const layer = document.createElement('div'); layer.className = 'scan'; layer.setAttribute('aria-hidden', 'true'); document.body.prepend(layer);
  let last = '';
  addEventListener('pointermove', e => {
    const x = Math.floor(e.pageX / 32) * 32, y = Math.floor(e.pageY / 32) * 32, key = x + ',' + y;
    if (key === last) return; last = key;
    const c = document.createElement('i'); c.style.left = x + 'px'; c.style.top = y + 'px';
    layer.append(c); setTimeout(() => c.remove(), 1200);
  }, { passive: true });
})();
</script>"""


SCRIPT = r"""
<script>
(() => {
  const calm = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Section titles arrive the way a language model writes: token by token, behind a cursor
  if (!calm && 'IntersectionObserver' in window) {
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (!e.isIntersecting) return; io.unobserve(e.target);
      const el = e.target, text = el.dataset.full, toks = text.match(/.{1,3}/g);
      let i = 0; el.textContent = ''; el.classList.add('streaming');
      const tick = () => {
        if (i >= toks.length) { el.classList.remove('streaming'); return; }
        const t = document.createElement('b'); t.textContent = toks[i++]; el.append(t);
        setTimeout(tick, 70 + Math.random() * 90);
      };
      tick();
    }), { threshold: 1 });
    document.querySelectorAll('main > section > h2 > span:first-child').forEach(el => {
      el.dataset.full = el.textContent; el.setAttribute('aria-label', el.textContent); el.textContent = ''; io.observe(el);
    });
  }


  // Hero: the three words and the three places pick the same direction; the player walks there, a dialogue box opens beside it, a second click closes it
  const picks = [...document.querySelectorAll('.zone, .kw')], player = document.querySelector('.player');
  function choose(k, first, swiped) {
    picks.forEach(b => b.setAttribute('aria-pressed', b.dataset.k === k));
    document.querySelectorAll('.zcap').forEach(c => c.hidden = c.dataset.k !== k);
    const bb = document.querySelector('.bubble');
    if (bb) bb.dataset.k = k || '';
    document.querySelectorAll('.zscene').forEach(s => s.classList.toggle('dim', !!k && s.dataset.k !== k));
    document.querySelector('.map-hero')?.classList.toggle('picked', !!k);
    const z = k && document.querySelector(`.zone[data-k="${k}"]`);
    if (player && z) {
      player.style.setProperty('--px', z.style.getPropertyValue('--x'));
      if (!first) { player.classList.add('walking'); setTimeout(() => player.classList.remove('walking'), 1100); }
      const m = document.querySelector('.map');
      if (!swiped && m.scrollWidth > m.clientWidth) m.scrollTo({ left: parseFloat(z.style.getPropertyValue('--x')) / 100 * m.scrollWidth - m.clientWidth / 2, behavior: first ? 'auto' : 'smooth' });
    }
  }
  let cur = null;
  picks.forEach(b => b.addEventListener('click', () => { cur = cur === b.dataset.k ? null : b.dataset.k; choose(cur); }));
  // Phone: the map scrolls sideways; while a dialogue is open, swiping hands it to the place now in the middle of the view
  const map = document.querySelector('.map');
  let settle;
  map?.addEventListener('scroll', () => {
    clearTimeout(settle);
    settle = setTimeout(() => {
      if (!cur || map.scrollWidth <= map.clientWidth) return;
      const mid = (map.scrollLeft + map.clientWidth / 2) / map.scrollWidth * 100;
      let best = cur, gap = Infinity;
      document.querySelectorAll('.zone').forEach(z => { const d = Math.abs(parseFloat(z.style.getPropertyValue('--x')) - mid); if (d < gap) { gap = d; best = z.dataset.k; } });
      if (best !== cur) { cur = best; choose(cur, false, true); }
    }, 150);
  }, { passive: true });

  // Experience: timeline blocks and save slots highlight each other
  const pair = k => [...document.querySelectorAll(`.blk[data-k="${k}"], .slot[data-k="${k}"]`)];
  document.querySelectorAll('.blk, .slot').forEach(el => {
    el.addEventListener('mouseenter', () => pair(el.dataset.k).forEach(x => x.classList.add('hl')));
    el.addEventListener('mouseleave', () => pair(el.dataset.k).forEach(x => x.classList.remove('hl')));
  });
  document.querySelectorAll('.blk').forEach(b => b.addEventListener('click', () => {
    const s = document.getElementById('x-' + b.dataset.k); s.classList.remove('flash'); void s.offsetWidth; s.classList.add('flash');
  }));

  // TL;DR toggles
  document.querySelectorAll('button.tldr').forEach(b => b.addEventListener('click', () => {
    const t = document.getElementById(b.getAttribute('aria-controls')), on = b.getAttribute('aria-expanded') !== 'true';
    b.setAttribute('aria-expanded', on); t.hidden = !on;
  }));

  // Publication filters (by topic); the scene links filter too
  const filters = [...document.querySelectorAll('.filters button')], count = document.querySelector('.count');
  function filter(k) {
    filters.forEach(x => x.setAttribute('aria-pressed', x.dataset.topic === k));
    let n = 0;
    document.querySelectorAll('.pub').forEach(li => { const on = k === 'all' || li.dataset.topic === k; li.hidden = !on; n += on; });
    document.querySelectorAll('.year').forEach(y => y.hidden = !y.querySelector('.pub:not([hidden])'));
    count.textContent = n + (n === 1 ? ' PAPER' : ' PAPERS');
  }
  filters.forEach(f => f.addEventListener('click', () => filter(f.dataset.topic)));
  document.querySelectorAll('.see').forEach(a => a.addEventListener('click', () => filter(a.dataset.topic)));
})();
</script>"""


SCENES = {"internals": lambda: scene_internals(), "simulation": lambda: scene_simulation(),
          "satellite": lambda: scene_satellite()}
TODAY = __import__("datetime").date.today().strftime("%Y-%m")


def rel(url: str, prefix: str) -> str:
    """Make a site-relative link work from a page `prefix` levels down."""
    return url if re.match(r"^(https?:|mailto:|#|/)", url) else prefix + url


THEME_INIT = "<script>try{const t=localStorage.getItem('theme');if(t)document.documentElement.dataset.theme=t;}catch(_){}</script>"
SUN = ["...A....", ".A.A.A..", "..AAA...", "AAAAAAA.", "..AAA...", ".A.A.A..", "...A....", "........"]
MOON = ["..XXX...", ".XX.....", "XX......", "XX......", "XX......", ".XX.....", "..XXX...", "........"]


def profile_nav(prefix: str = "") -> str:
    items = [l for l in site.get("profiles", []) if l.get("url")]
    toggle = (f'<button type="button" class="btn theme" aria-label="Switch day and night">'
              f'{sprite(SUN, {"A": "#13a374"}, "sun")}{sprite(MOON, {"X": "#ececf1"}, "moon")}</button>')
    return "".join(f'<a class="btn" href="{h(rel(l["url"], prefix))}"{ext(l["url"])}>{h(l["label"])}</a>' for l in items) + toggle


def head(title: str, desc: str, path: str, prefix: str = "") -> str:
    url = "https://chaeminjang.com/" + path
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#f6f6f4">
  <meta name="description" content="{h(desc)}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{h(title)}">
  <meta property="og:description" content="{h(desc)}">
  <meta property="og:image" content="{h(site['og_image'])}">
  <meta property="og:url" content="{url}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="canonical" href="{url}">
  <link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
  {fonts(prefix)}
  {css(prefix, "style.css")}
  {THEME_INIT}
  <title>{h(title)}</title>
</head>"""


def top_bar(prefix: str = "") -> str:
    return f"""  <header class="top">
    <p class="logo"><a href="{prefix or './'}">CHAEMIN<span>.</span>JANG</a></p>
    <nav aria-label="Profiles">{profile_nav(prefix)}</nav>
  </header>"""


def footer() -> str:
    me = sprite(ME_SPRITE, ME_COLORS, "foot-me")
    return (f'  <footer><span>&copy; {h(site["footer_year"])} {h(site["name"])}</span>'
            f'<a class="to-top" href="#" aria-label="Back to top">{me}<span>CONTINUE?</span><b aria-hidden="true">&#9650;</b></a></footer>')


ZONE = {"internals": "INSIDE", "simulation": "PEOPLE", "satellite": "FIELD"}


def avatar() -> str:
    return f"""<figure class="avatar px" title="Hover for the pixel version">
      <img src="assets/images/portrait-square.jpg" width="320" height="320" alt="Chaemin Jang">
      {sprite(ME_SPRITE, ME_COLORS, "me-sprite")}
    </figure>"""


def zone_caption(k, counts) -> str:
    t = TOPICS[k]
    return (f'<div class="zcap" data-k="{k}" hidden><p class="look">{h(t["look"])}</p>'
            f'<p class="what">{h(t["line"])}</p><div class="actions"><a class="act primary" href="research/#{k}">Read more →</a>'
            + (f'<a class="act see" href="#pubs-h" data-topic="{k}">{counts[k]} paper{"s" if counts[k] != 1 else ""} ↓</a>' if counts[k] else "")
            + (f'<a class="act" href="#proj-h">{project_count(k)} project{"s" if project_count(k) != 1 else ""} ↓</a>' if project_count(k) else "")
            + '</div></div>')


def hero(ps) -> str:
    """Name and one-line statement on top; below it a pixel world with one place per research direction."""
    counts = {k: sum(topic_of(p) == k for p in ps) for k in TOPICS}
    start = '<p class="start-wrap"><a class="start" href="research/"><span class="tri" aria-hidden="true"></span>PRESS START<span class="sub">RESEARCH OVERVIEW</span></a></p>'
    W = 300
    g = [f'<svg class="pano" viewBox="0 14 {W} 70" shape-rendering="crispEdges" aria-hidden="true"><rect width="{W}" height="96" class="sky"/>']
    for cx, cy in ((96, 20), (190, 16), (284, 22)):
        g.append(f'<rect x="{cx}" y="{cy}" width="14" height="3" class="cloud"/><rect x="{cx + 3}" y="{cy - 2}" width="7" height="2" class="cloud"/>')
    for x in range(W):
        hh = int(6 + 4 * math.sin(x / 23) + 3 * math.sin(x / 9))
        g.append(f'<rect x="{x}" y="{70 - hh}" width="1" height="{hh}" class="hill"/>')
    stars = ((14, 30), (40, 18), (62, 34), (118, 28), (150, 22), (170, 36), (214, 26), (236, 17), (262, 32), (296, 27))
    g.append('<g class="night"><rect x="21" y="17" width="6" height="10" class="moon"/><rect x="19" y="19" width="10" height="6" class="moon"/><rect x="20" y="18" width="8" height="8" class="moon"/>'
             '<rect x="24" y="15" width="6" height="10" class="sky"/><rect x="22" y="17" width="10" height="6" class="sky"/><rect x="23" y="16" width="8" height="8" class="sky"/>'
             + "".join(f'<rect x="{x}" y="{y}" width="1" height="1" class="star" style="--d:{i * .37 % 2.6:.2f}s"/>' for i, (x, y) in enumerate(stars)) + '</g>')
    g.append(f'<rect x="0" y="70" width="{W}" height="26" class="ground"/>')
    g += [f'<rect x="{x}" y="78" width="3" height="1" class="path"/>' for x in range(0, W, 6)]
    for i, k in enumerate(TOPICS):
        sw = {"internals": 78, "simulation": 94, "satellite": 90}[k]; sh = sw / 2
        g.append(f'<svg class="zscene play" data-k="{k}" x="{52 + i * 100 - sw / 2:.1f}" y="{69 - sh * 0.975:.1f}" width="{sw}" height="{sh}" viewBox="0 0 80 40">{SCENES[k]()}</svg>')
    g.append('<rect x="244" y="69" width="44" height="2" class="soil"/>')
    g.append("</svg>")
    zones = "".join(f'<button type="button" class="zone" data-k="{k}" style="--x:{(52 + i * 100) / W * 100:.2f}%" aria-pressed="false">'
                    f'<span class="board">{ticon(k)}{ZONE[k]}</span><span class="post"></span></button>' for i, k in enumerate(TOPICS))
    kw = {k: f'<button type="button" class="kw" data-k="{k}" aria-pressed="false">{ticon(k)}{w}</button>'
          for k, w in (("internals", "inside"), ("simulation", "people"), ("satellite", "field"))}
    return f"""  <section class="hero map-hero v-console" aria-label="Introduction">
    <div class="screenwrap"><div class="led"><i></i>POWER</div><div class="glass"><div class="world"><div class="map"><div class="inner">{"".join(g)}<span class="player">{sprite(ME_SPRITE, ME_COLORS, "pl")}</span>{zones}</div></div><div class="zcaps bubble">{"".join(zone_caption(k, counts) for k in TOPICS)}</div></div>
    <p class="map-hint" aria-hidden="true">◀ SWIPE THE MAP ▶</p><div class="dlg"><p class="speaker">CHAEMIN</p><p class="big">I study language models from the <span class="nw">{kw["internals"]},</span> as stand-ins for <span class="nw">{kw["simulation"]},</span> and out in the <span class="nw">{kw["satellite"]}.</span></p><span class="more" aria-hidden="true"></span></div></div><p class="brand">PIXEL RESEARCH SYSTEM</p></div>
    <div class="body"><div class="hello"><div class="who">{avatar()}<div><h1>Chaemin Jang</h1><p class="role">M.S. Student · KAIST School of Computing</p><p class="adv">Advised by Jihee Kim and Dongman Lee.</p></div></div></div><div class="ctl">{start}<span class="ab" aria-hidden="true"><b>B</b><b>A</b></span></div></div>
  </section>"""


def render() -> str:
    ps = order(papers)
    filters = '<button type="button" data-topic="all" aria-pressed="true">ALL</button>' + "".join(
        f'<button type="button" data-topic="{k}" aria-pressed="false">{h(t["name"].upper())}</button>' for k, t in TOPICS.items()
        if any(topic_of(p) == k for p in ps))
    return head(site["name"], site["home_description"], "") + f"""
<body>
<main class="home">
{top_bar()}

{hero(ps)}

{news_block(TODAY)}

  <section aria-labelledby="pubs-h">
    <h2 id="pubs-h"><span>PUBLICATIONS</span><small class="count">{len(ps)} PAPERS</small></h2>
    <div class="filters" role="group" aria-label="Filter by topic">{filters}</div>
    <div class="pubs px">{publications(ps)}</div>
  </section>

{projects_block()}

  <section aria-labelledby="log-h">
    <h2 id="log-h"><span>EXPERIENCE</span></h2>
    {experience_block()}
  </section>

{footer()}
</main>
{SCRIPT}
{SCAN}
</body>
</html>
"""


def research_paper(p: dict, prefix: str) -> str:
    k = key_of(p)
    aid = arxiv_id(p)
    r = research.get(k, {})
    links = [f'<a class="btn primary" href="{h(rel(p["url"], prefix))}"{ext(p["url"])}>Read {"abstract" if p.get("url_label") == "Abstract" else "paper"}</a>'] if p.get("url") else []
    if aid:
        links.append(f'<a class="btn" href="https://arxiv.org/pdf/{aid}"{ext("https://")}>PDF</a>')
    for i in p.get("links", []):
        if i["label"].lower() == "project":
            links.append(f'<a class="btn" href="{h(rel(i["url"], prefix))}">Project page</a>')
    note = f'<p class="note">{h(p["note"])}</p>' if p.get("note") else ""
    summary = f'<p class="summary">{h(r["summary"])}</p>' if r.get("summary") else ""
    kind = "preprint" if is_preprint(p) else "published"
    return f"""
        <article class="rpaper">
          <p class="meta"><span class="tag {kind}">{h(short_venue(p).replace(chr(10), " · "))}</span><span class="yr">{year_of(p)}</span></p>
          <h4>{nb(p['title'])}</h4>
          <p class="who">{authors(p)}</p>
          {award_line(p)}{note}{summary}
          <p class="btns">{''.join(links)}</p>
        </article>"""


def research_papers(mine, pre):
    if not mine:
        return ""
    return f'<h3 class="papers-h">PAPERS <small>{len(mine)}</small></h3>' + "".join(research_paper(p, pre) for p in mine)


def research_projects(k):
    mine = [pr for pr in projects if pr.get("topic") == k]
    if not mine:
        return ""
    rows = "".join(f"""
        <article class="rpaper">
          <p class="meta"><span class="tag">PROJECT</span><span class="yr">{h(pr['period'])}</span></p>
          <h4>{h(pr['title'])}</h4>
          <p class="who">{h(pr['partner'])}</p>
          <p class="summary">{h(pr['line'])}</p>
          <p class="btns"><a class="btn primary" href="../projects/{h(pr['slug'])}/">Project details</a></p>
        </article>""" for pr in mine)
    return f'<h3 class="papers-h">PROJECTS <small>{len(mine)}</small></h3>{rows}'


def render_research() -> str:
    ps = order(papers)
    pre = "../"
    toc = "".join(f'<a href="#{k}"><span class="num">{i + 1:02d}</span>{h(t["name"])}</a>' for i, (k, t) in enumerate(TOPICS.items()))
    sections = []
    for i, (k, t) in enumerate(TOPICS.items()):
        mine = [p for p in ps if topic_of(p) == k]
        qs = "".join(f"<li>{h(q)}</li>" for q in t.get("questions", []))
        sections.append(f"""
  <section class="direction" id="{k}" aria-labelledby="{k}-h">
    <div class="dir-head px">
      <div class="scene play">
        <svg viewBox="0 0 80 40" shape-rendering="crispEdges" role="img" aria-label="{h(t['look'])}">{SCENES[k]()}</svg>
      </div>
      <div class="dir-text">
        <p class="look"><span class="num">{i + 1:02d}</span> {h(t['look'])}</p>
        <h2 id="{k}-h">{h(t['name'])}</h2>
        <p class="lede">{h(t['intro'])}</p>
      </div>
    </div>
    <div class="questions"><h3>QUESTIONS</h3><ol>{qs}</ol></div>
    {research_papers(mine, pre)}
    {research_projects(k)}
  </section>""")
    return head(f"Research · {site['name']}", topics_data["overview"], "research/", pre) + f"""
<body class="research-page">
<main>
{top_bar(pre)}

  <p class="crumb"><a href="../"><span class="arrow">←</span> HOME</a></p>
  <section class="overview">
    <h1>Research</h1>
    <p>{h(topics_data['overview'])}</p>
    <nav class="toc" aria-label="Directions">{toc}</nav>
  </section>
{''.join(sections)}

{footer()}
</main>
{SCAN}
</body>
</html>
"""


def render_project_page(pr: dict) -> str:
    pre = "../../"
    t = TOPICS.get(pr.get("topic"), {"name": ""})
    paras = "".join(f"<p>{h(x)}</p>" for x in pr.get("summary", [pr["line"]]))
    facts = [("Funding", pr["partner"]), ("Period", pr["period"])]
    if pr.get("team"):
        facts.append(("Team", pr["team"]))
    if pr.get("role"):
        facts.append(("My role", pr["role"]))
    dl = "".join(f"<dt>{h(a)}</dt><dd>{h(b)}</dd>" for a, b in facts)
    btns = "".join(f'<a class="btn" href="{h(l["url"])}"{ext(l["url"])}>{h(l["label"])}</a>' for l in pr.get("links", []))
    related = [p for p in order(papers) if arxiv_id(p) in pr.get("papers", [])]
    rel_html = (f'<h3 class="papers-h">RELATED PAPERS <small>{len(related)}</small></h3>'
                + "".join(research_paper(p, pre) for p in related)) if related else ""
    img = pr.get("image")
    fig = (f'<figure class="pfig px"><img src="{pre}{h(img["src"])}" alt="{h(img["alt"])}" loading="lazy">'
           f'<figcaption>{h(img.get("caption", ""))}</figcaption></figure>') if img else ""
    secs = []
    for sec in pr.get("sections", []):
        body = "".join(f"<p>{h(x)}</p>" for x in sec.get("paras", []))
        if sec.get("bullets"):
            body += "<ul>" + "".join(f"<li>{h(b)}</li>" for b in sec["bullets"]) + "</ul>"
        secs.append(f'<div class="psec"><h3 class="papers-h">{h(sec["heading"].upper())}</h3>{body}</div>')
    secs_html = "".join(secs)
    return head(f"{pr['title']} · {site['name']}", pr["line"], f"projects/{pr['slug']}/", pre) + f"""
<body class="research-page">
<main>
{top_bar(pre)}

  <p class="crumb"><a href="../../#proj-h"><span class="arrow">←</span> PROJECTS</a></p>
  <section class="overview project-head">
    <p class="look"><a href="../../research/#{h(pr['topic'])}">{tname(t, upper=True)}</a></p>
    <h1 class="ptitle">{h(pr['title'])}</h1>
    <div class="psum">{paras}</div>
    <dl class="facts px">{dl}</dl>
    {f'<p class="btns">{btns}</p>' if btns else ""}
  </section>
  <section class="direction">
    {fig}
    {secs_html}
    {rel_html}
  </section>

{footer()}
</main>
{SCAN}
</body>
</html>
"""


PAPER_PAGES = {"project-page.html": "icl-suppresses-knowledge-recall", "paper-who-differs.html": "who-differs"}


def build_project(src: str = "project-page.html", slug: str = "icl-suppresses-knowledge-recall") -> None:
    """A paper page (content/<src> -> papers/<slug>/), restyled. Figures whose image is missing are left out."""
    source = (CONTENT / src).read_text(encoding="utf-8")
    page = source.replace('<link rel="stylesheet" href="../../assets/css/site.css">',
                          fonts('../../') + css('../../', "style.css") + css('../../', "project.css"))
    page = page.replace('<body id="top">', '<body id="top" class="project-page">')
    page = page.replace("</body>", SCAN + "\n</body>")
    page = page.replace('<meta name="color-scheme" content="light">', '<meta name="color-scheme" content="light dark">')
    url = f"https://chaeminjang.com/papers/{slug}/"
    social = (f'  <meta property="og:url" content="{url}">\n  <meta property="og:image" content="{h(site["og_image"])}">\n'
              f'  <meta name="twitter:card" content="summary_large_image">\n  <link rel="canonical" href="{url}">\n')
    page = page.replace("</head>", social + THEME_INIT + "\n</head>", 1)

    def keep_figure(m):
        src = re.search(r'src="\.\./\.\./([^"]+)"', m.group(0))
        return m.group(0) if src and (ROOT / src.group(1)).exists() else ""
    page = re.sub(r'<figure class="project-figure">.*?</figure>', keep_figure, page, flags=re.S)
    dest = ROOT / "papers" / slug / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(page, encoding="utf-8")


def render_404() -> str:
    """Served by GitHub Pages for any missing path, so every link is root-absolute."""
    return head("Game over — " + site["name"], "This page does not exist.", "404.html", "/") + f"""
<body>
<main class="lost">
{top_bar("/")}
  <section class="over px" aria-labelledby="over-h">
    {sprite(ME_SPRITE, ME_COLORS, "over-me")}
    <h1 id="over-h">GAME OVER</h1>
    <p class="why">404 · this page does not exist</p>
    <p class="cont-q">CONTINUE? <span id="count">9</span></p>
    <p><a class="start" href="/"><span class="tri" aria-hidden="true"></span>PRESS START<span class="sub">BACK TO HOME</span></a></p>
  </section>
</main>
<script>
(() => {{
  const c = document.getElementById('count'); let n = 9;
  const t = setInterval(() => {{ n -= 1; c.textContent = n; if (n === 0) {{ clearInterval(t); c.parentElement.textContent = 'INSERT COIN'; }} }}, 1000);
}})();
</script>
{SCAN}
</body>
</html>
"""


if __name__ == "__main__":
    unknown = [k for k in research if not k.startswith("_") and k not in {key_of(p) for p in papers}]
    if unknown:
        print(f"note: research.json has entries with no matching paper: {unknown}")
    (ROOT / "index.html").write_text(render(), encoding="utf-8")
    (ROOT / "404.html").write_text(render_404(), encoding="utf-8")
    (ROOT / "research").mkdir(exist_ok=True)
    (ROOT / "research" / "index.html").write_text(render_research(), encoding="utf-8")
    for src, slug in PAPER_PAGES.items():
        build_project(src, slug)
    for pr in projects:
        d = ROOT / "projects" / pr["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(render_project_page(pr), encoding="utf-8")
    pages = ["", "research/"] + [f"projects/{pr['slug']}/" for pr in projects] + [f"papers/{slug}/" for slug in PAPER_PAGES.values()]
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + "".join(f"  <url><loc>https://chaeminjang.com/{p}</loc></url>\n" for p in pages) + "</urlset>\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: https://chaeminjang.com/sitemap.xml\n", encoding="utf-8")
    print("Built index.html, research/index.html, papers/*/index.html, sitemap.xml")
