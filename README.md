# Chaemin Jang — refined research chapters

Open index.html in a browser or deploy this folder to GitHub Pages.

The Publications section keeps the two research directions and sticky desktop
headings. This refinement gives chapter headings a stronger scale, restores bold
paper titles, strengthens dividing rules, and adjusts row alignment and spacing.
Compound words in titles do not break across lines. On mobile, chapter headings
sit above the papers, and venues align below the author information.

The portrait, introduction, contact links, Experience section and footer are
unchanged. Paper titles, authors, notes, destinations and ordering are preserved.
No new controls, animations, external fonts, or JavaScript were added.

## Editing
Update content/site.json, content/publications.json or content/experience.json
and run `python3 build.py`. The build uses only Python's standard library.

The scoped chapter styles are at the end of assets/css/vignelli.css. A standalone
copy is provided in research-chapters.css for review; edit the main stylesheet
when changing the deployed page. All chapter rules are scoped to .publications.

Desktop sticky headings are enabled above 900px, and are bounded by their own
research section. Reduced-motion preferences and visible keyboard focus are
preserved.
