# brazil2026

GitHub Pages site for the Rio 2026 itinerary.

Live URL:

`https://dburkhardt.github.io/brazil2026/`

Structure:

- [index.html](/Users/dburkhardt/git-repos/brazil2026/index.html) is the homepage with one card per day.
- [social-share.jpg](/Users/dburkhardt/git-repos/brazil2026/social-share.jpg) is the photo-based Open Graph and Twitter share image.
- [slides.html](/Users/dburkhardt/git-repos/brazil2026/slides.html) preserves the original slide-deck version.
- [scripts/build_site.py](/Users/dburkhardt/git-repos/brazil2026/scripts/build_site.py) regenerates the homepage and all day pages from `slides.html`.

To rebuild after itinerary edits:

```bash
python3 scripts/build_site.py
```
