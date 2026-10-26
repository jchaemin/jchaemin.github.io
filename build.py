#!/usr/bin/env python3
"""Build the homepage and the COLM project page.

Content lives in content/:
  site.json          name, links, intro text
  publications.json  paper metadata (title, authors, venue, links)
  research.json      per paper: what the model knows, what it does, evidence
  experience.json    roles
Run:  python3 build.py      (standard library only)
"""
from __future__ import annotations

import html
import json
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
ME = site["featured_author"]

def fonts(prefix: str = "") -> str:
    return (f'<link rel="preload" href="{prefix}assets/fonts/pixelify-sans-latin-500-normal.woff2" as="font" type="font/woff2" crossorigin>'
            f'<link rel="stylesheet" href="{prefix}assets/css/fonts.css">')


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
    return sorted(ps, key=lambda p: (-year_of(p), -float(arxiv_id(p) or 0)))


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
LLM_CLS = {"O": "ink", "L": "shell", "d": "ink", "Z": "eye", "A": "acc", "E": "acc"}


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


def pub_row(p: dict) -> str:
    k = key_of(p)
    aid = arxiv_id(p)
    r = research.get(k, {})
    links = [f'<a href="{h(p["url"])}"{ext(p["url"])}>{"arXiv" if aid else "Paper"}</a>']
    if aid:
        links.append(f'<a href="https://arxiv.org/pdf/{aid}"{ext("https://")}>PDF</a>')
    for i in p.get("links", []):
        if i["label"].lower() == "project":
            links.append(f'<a href="{h(i["url"])}">Project</a>')
        elif i["url"].rstrip("/") != p["url"].rstrip("/") and i["label"].lower() not in ("paper",):
            links.append(f'<a href="{h(i["url"])}"{ext(i["url"])}>{h(i["label"])}</a>')
    tldr_btn = (f'<button type="button" class="tldr" aria-expanded="false" aria-controls="t-{h(k)}">TL;DR</button>'
                if r.get("line") else "")
    tldr = f'<p class="tldr-text" id="t-{h(k)}" hidden>{h(r["line"])}</p>' if r.get("line") else ""
    note = f'<p class="note">{h(p["note"])}</p>' if p.get("note") else ""
    kind = "preprint" if is_preprint(p) else "published"
    return f"""
        <li class="pub" id="p-{h(k)}" data-kind="{kind}" data-topic="{topic_of(p)}">
          <span class="tag {kind}">{h(short_venue(p))}</span>
          <div>
            <h3><a href="{h(p['url'])}"{ext(p['url'])}>{nb(p['title'])}</a></h3>
            <p class="who">{authors(p)}</p>
            {note}
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


def topic_panel(ps) -> str:
    counts = {k: sum(topic_of(p) == k for p in ps) for k in TOPICS}
    tabs = "".join(
        f'<button type="button" role="tab" id="tab-{k}" aria-controls="scene-{k}" aria-selected="{str(i == 0).lower()}" data-topic="{k}">'
        f'<span class="num">{i + 1:02d}</span>{h(t["name"])}</button>'
        for i, (k, t) in enumerate(TOPICS.items()))
    scenes = "".join(f"""
      <div class="scene" id="scene-{k}" role="tabpanel" aria-labelledby="tab-{k}"{'' if i == 0 else ' hidden'}>
        <svg viewBox="0 0 80 40" shape-rendering="crispEdges" role="img" aria-label="{h(t['look'])}">{SCENES[k]()}</svg>
        <div class="caption">
          <p class="look">{h(t['look'])}</p>
          <p class="what">{h(t['line'])}</p>
          <div class="actions">
            <a class="act primary" href="research/#{k}">Read about this direction →</a>
            <a class="act see" href="#pubs-h" data-topic="{k}">Show its {counts[k]} paper{'s' if counts[k] != 1 else ''} ↓</a>
          </div>
        </div>
      </div>""" for i, (k, t) in enumerate(TOPICS.items()))
    return f'<div class="tabs" role="tablist" aria-label="Research topics">{tabs}</div>{scenes}'


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


SCRIPT = r"""
<script>
(() => {
  // Topic scenes: two ways of looking at the same model
  const tabs = [...document.querySelectorAll('.tabs [role=tab]')];
  const play = el => { el.classList.remove('play'); void el.offsetWidth; el.classList.add('play'); };
  function pick(k) {
    tabs.forEach(t => t.setAttribute('aria-selected', t.dataset.topic === k));
    document.querySelectorAll('.scene').forEach(s => { const on = s.id === 'scene-' + k; s.hidden = !on; if (on) play(s); });
  }
  tabs.forEach((t, i) => {
    t.addEventListener('click', () => pick(t.dataset.topic));
    t.addEventListener('keydown', e => {
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') { const n = tabs[(i + (e.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length]; n.focus(); pick(n.dataset.topic); }
    });
  });
  play(document.querySelector('.scene:not([hidden])'));

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


SCENES = {"internals": lambda: scene_internals(), "simulation": lambda: scene_simulation()}


def rel(url: str, prefix: str) -> str:
    """Make a site-relative link work from a page `prefix` levels down."""
    return url if re.match(r"^(https?:|mailto:|#|/)", url) else prefix + url


def profile_nav(prefix: str = "") -> str:
    items = [l for l in site.get("profiles", []) if l.get("url")]
    return "".join(f'<a class="btn" href="{h(rel(l["url"], prefix))}"{ext(l["url"])}>{h(l["label"])}</a>' for l in items)


def head(title: str, desc: str, path: str, prefix: str = "") -> str:
    url = "https://jchaemin.github.io/" + path
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
  <link rel="stylesheet" href="{prefix}assets/css/style.css">
  <title>{h(title)}</title>
</head>"""


def top_bar(prefix: str = "") -> str:
    return f"""  <header class="top">
    <p class="logo"><a href="{prefix or './'}">CHAEMIN<span>.</span>JANG</a></p>
    <nav aria-label="Profiles">{profile_nav(prefix)}</nav>
  </header>"""


def footer() -> str:
    return f'  <footer><span>&copy; {h(site["footer_year"])} {h(site["name"])}</span></footer>'


def render() -> str:
    ps = order(papers)
    filters = '<button type="button" data-topic="all" aria-pressed="true">ALL</button>' + "".join(
        f'<button type="button" data-topic="{k}" aria-pressed="false">{h(t["name"].upper())}</button>' for k, t in TOPICS.items())
    return head(site["name"], site["home_description"], "") + f"""
<body>
<main>
{top_bar()}

  <section class="intro" aria-label="Introduction">
    <figure class="avatar px" title="Hover for the pixel version">
      <img src="assets/images/portrait-square.jpg" width="320" height="320" alt="Chaemin Jang">
      {sprite(ME_SPRITE, ME_COLORS, "me-sprite")}
    </figure>
    <div>
      <h1>Chaemin Jang</h1>
      <p class="role">M.S. Student · KAIST School of Computing</p>
      <p>Advised by Jihee Kim and Dongman Lee. I study language models from two sides:
      what happens inside them, and how well they stand in for people. <a class="more" href="research/">Research overview →</a></p>
    </div>
  </section>

  <section class="topics px" aria-label="Research topics">{topic_panel(ps)}</section>

  <section aria-labelledby="pubs-h">
    <h2 id="pubs-h"><span>PUBLICATIONS</span><small class="count">{len(ps)} PAPERS</small></h2>
    <div class="filters" role="group" aria-label="Filter by topic">{filters}</div>
    <div class="pubs px">{publications(ps)}</div>
  </section>

  <section aria-labelledby="log-h">
    <h2 id="log-h"><span>EXPERIENCE</span></h2>
    {experience_block()}
  </section>

{footer()}
</main>
{SCRIPT}
</body>
</html>
"""


def research_paper(p: dict, prefix: str) -> str:
    k = key_of(p)
    aid = arxiv_id(p)
    r = research.get(k, {})
    links = [f'<a class="btn primary" href="{h(p["url"])}"{ext(p["url"])}>Read paper</a>']
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
          <p class="meta"><span class="tag {kind}">{h(short_venue(p))}</span><span class="yr">{year_of(p)}</span></p>
          <h4>{nb(p['title'])}</h4>
          <p class="who">{authors(p)}</p>
          {note}{summary}
          <p class="btns">{''.join(links)}</p>
        </article>"""


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
    <h3 class="papers-h">PAPERS <small>{len(mine)}</small></h3>
    {''.join(research_paper(p, pre) for p in mine)}
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
</body>
</html>
"""


def build_project() -> None:
    """The COLM project article, restyled. Figures whose image is missing are left out."""
    source = (CONTENT / "project-page.html").read_text(encoding="utf-8")
    page = source.replace('<link rel="stylesheet" href="../../assets/css/site.css">',
                          fonts('../../') + '<link rel="stylesheet" href="../../assets/css/style.css"><link rel="stylesheet" href="../../assets/css/project.css">')
    page = page.replace('<body id="top">', '<body id="top" class="project-page">')
    page = page.replace('<meta name="color-scheme" content="light">', '<meta name="color-scheme" content="light dark">')

    def keep_figure(m):
        src = re.search(r'src="\.\./\.\./([^"]+)"', m.group(0))
        return m.group(0) if src and (ROOT / src.group(1)).exists() else ""
    page = re.sub(r'<figure class="project-figure">.*?</figure>', keep_figure, page, flags=re.S)
    dest = ROOT / "papers" / "icl-suppresses-knowledge-recall" / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(page, encoding="utf-8")


if __name__ == "__main__":
    unknown = [k for k in research if not k.startswith("_") and k not in {key_of(p) for p in papers}]
    if unknown:
        print(f"note: research.json has entries with no matching paper: {unknown}")
    (ROOT / "index.html").write_text(render(), encoding="utf-8")
    (ROOT / "research").mkdir(exist_ok=True)
    (ROOT / "research" / "index.html").write_text(render_research(), encoding="utf-8")
    build_project()
    print("Built index.html, research/index.html and papers/icl-suppresses-knowledge-recall/index.html")
