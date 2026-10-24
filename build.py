#!/usr/bin/env python3
"""Build a clean, self-contained Vignelli-inspired research site.

Edit content/site.json, publications.json, or experience.json, then run:
    python3 build.py

No network access, packages, build frameworks, or templates are required.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
site = json.loads((CONTENT / "site.json").read_text(encoding="utf-8"))
papers = json.loads((CONTENT / "publications.json").read_text(encoding="utf-8"))
experience = json.loads((CONTENT / "experience.json").read_text(encoding="utf-8"))


def h(value: str) -> str:
    return html.escape(str(value), quote=True)


def target(url: str) -> str:
    return ' target="_blank" rel="noopener noreferrer"' if url.startswith(('https://', 'http://')) else ''


def a(url: str, label: str, **kwargs) -> str:
    attrs = ' '.join(f'{k.replace("_", "-")}="{h(v)}"' for k, v in kwargs.items())
    return f'<a href="{h(url)}"{target(url)} {attrs}>{label}</a>'


def social_links() -> str:
    items = [
        ('Google Scholar', site['scholar_url']),
        ('GitHub', site['github_url']),
        ('CV', 'assets/cv/cv.pdf'),
        ('Email', f"mailto:{site['email']}"),
    ]
    return '\n'.join(
        a(url, h(label), aria_label=label)
        for label, url in items
    )


def authors(names: list[str]) -> str:
    featured = site['featured_author']
    return ', '.join(f'<strong>{h(n)}</strong>' if n == featured else h(n) for n in names)


def paper_title(title: str) -> str:
    """Keep compound words intact without changing the title text."""
    formatted = h(title)
    for term in ('Label-Free', 'In-Context', 'Instruction-Tuned'):
        formatted = formatted.replace(term, f'<span class="paper-phrase">{term}</span>')
    return formatted


def publications() -> str:
    """Group papers by research direction, retaining the original publication row.

    Edit `research_area` in content/publications.json to change a paper's group.
    The original JSON order is preserved within each group.
    """
    areas = (
        ('internals', 'llm-internals', 'LLM Internals', 'How models store, retrieve, and use knowledge.'),
        ('simulation', 'simulation', 'Simulation', 'How models reproduce distributions and human behavior.'),
    )
    valid = {area for area, _, _, _ in areas}
    if unknown := [p['title'] for p in papers if p.get('research_area') not in valid]:
        raise ValueError(f'Each paper needs a research_area: {unknown}')
    total = len(papers)
    sequence = 0
    blocks = []
    for area, group_id, title, tagline in areas:
        rows = []
        for paper in papers:
            if paper['research_area'] != area:
                continue
            sequence += 1
            links = []
            for item in paper.get('links', []):
                url = item['url']
                if url.rstrip('/') == paper['url'].rstrip('/'):
                    continue
                label = 'Project page' if item['label'].lower() == 'project' else item['label']
                links.append(a(url, h(label), aria_label=item.get('aria_label', item['label'])))
            extras = f'<nav class="paper-resources" aria-label="Resources for {h(paper["title"])}">{"".join(links)}</nav>' if links else ''
            note = f'<p class="paper-note">{h(paper["note"])}</p>' if paper.get('note') else ''
            rows.append(f'''<article class="paper" id="paper-{sequence:02d}">
              <div class="paper-index" aria-label="Publication {sequence} of {total}">{sequence:02d}</div>
              <div class="paper-copy">
                <h4>{a(paper['url'], paper_title(paper['title']))}</h4>
                <p class="paper-authors">{authors(paper['authors'])}</p>
                {note}
                {extras}
              </div>
              <p class="paper-venue">{h(paper['venue'])}</p>
            </article>''')
        blocks.append(f'''<section class="research-group" id="{group_id}" aria-labelledby="{group_id}-heading">
          <div class="research-group-heading">
            <h3 id="{group_id}-heading">{h(title)}</h3>
            <p>{h(tagline)}</p>
          </div>
          <div class="publication-list">{''.join(rows)}</div>
        </section>''')
    return ''.join(blocks)


def history() -> str:
    """Build two parallel work streams, with dates attached to every role.

    Experience items choose their track in content/experience.json. Within each
    track, items are sorted by start date. There is no legend or separate time axis.
    """
    groups = (("research", "Research"), ("industry", "Industry & ventures"))
    known = {key for key, _ in groups}
    unknown = [item.get("organization", "?") for item in experience if item.get("track") not in known]
    if unknown:
        raise ValueError(f"Experience entries need track 'research' or 'industry': {unknown}")
    columns = []
    for key, label in groups:
        selected = sorted(
            (item for item in experience if item["track"] == key),
            key=lambda item: int(item["start_year"]), reverse=True
        )
        records = []
        for item in selected:
            description = item.get("description", "")
            parts = description.split(" · ", 1)
            role = item.get("role") or (parts[0] if description else "")
            detail = item.get("detail") or (parts[1] if len(parts) > 1 else "")
            ongoing = item.get("end_year") is None
            date = item["date"].replace("–", "—")
            modifier = ' is-current' if ongoing else ''
            records.append(f'''<li class="experience-entry{modifier}">
              <div class="experience-date">{h(date)}</div>
              <div class="experience-entry-content">
                <h4 class="experience-org">{h(item['organization'])}</h4>
                <p class="experience-role">{h(role)}</p>
                <p class="experience-detail">{h(detail)}</p>
              </div>
            </li>''')
        columns.append(f'''<section class="experience-lane" aria-labelledby="experience-{key}">
          <h3 class="experience-lane-title" id="experience-{key}">{h(label)}</h3>
          <ol class="experience-entries">{''.join(records)}</ol>
        </section>''')
    return '<div class="experience-grid">' + ''.join(columns) + '</div>'


def render() -> str:
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <meta name="theme-color" content="#f8f8f6">
  <meta name="description" content="{h(site['home_description'])}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{h(site['name'])} — Research">
  <meta property="og:description" content="{h(site['og_description'])}">
  <meta property="og:image" content="{h(site['og_image'])}">
  <meta property="og:url" content="https://jchaemin.github.io/">
  <meta property="og:image:alt" content="Chaemin Jang — KAIST research">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="canonical" href="https://jchaemin.github.io/">
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="assets/css/vignelli.css">
  <title>{h(site['name'])} — Research</title>
</head>
<body>
<a class="skip-link" href="#publications">Skip to publications</a>
<div class="site-shell" id="top">
  <main>
    <section class="hero" aria-labelledby="name">
      <div class="identity">
        <h1 id="name">CHAEMIN<br>JANG</h1>
        <nav class="contact-links" aria-label="Research and contact">{social_links()}</nav>
      </div>
      <div class="intro">
        <p class="lead">{h(site['lead'])}</p>
        <p class="bio">{h(site['bio'])}</p>
      </div>
      <figure class="portrait">
        <img src="assets/images/portrait.jpg" width="900" height="900" alt="Portrait of Chaemin Jang" fetchpriority="high">
      </figure>
    </section>
    <section class="section publications" id="publications" aria-labelledby="publications-heading">
      <div class="section-heading">
        <h2 id="publications-heading">Selected publications</h2>
      </div>
      {publications()}
    </section>
    <section class="section background" aria-labelledby="background-heading">
      <div class="section-heading">
        <h2 id="background-heading">Experience</h2>
      </div>
      {history()}
    </section>
  </main>
  <footer class="site-footer"><span>© {h(site['footer_year'])} CHAEMIN JANG</span><a href="#top">BACK TO TOP ↑</a></footer>
</div>
</body>
</html>'''


def build_project() -> None:
    """Keep the existing project article intact, but apply this site's design."""
    source = (CONTENT / 'project-page.html').read_text(encoding='utf-8')
    page = source.replace('href="../../assets/css/site.css"', 'href="../../assets/css/vignelli.css"><link rel="stylesheet" href="../../assets/css/project.css"')
    page = page.replace('<body id="top">', '<body id="top" class="project-page">')
    page = page.replace('<meta name="theme-color" content="#fcfcfa">', '<meta name="theme-color" content="#f8f8f6">')
    dest = ROOT / 'papers' / 'icl-suppresses-knowledge-recall' / 'index.html'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(page, encoding='utf-8')


if __name__ == '__main__':
    (ROOT / 'index.html').write_text(render(), encoding='utf-8')
    build_project()
    print('Built index.html and papers/icl-suppresses-knowledge-recall/index.html')
