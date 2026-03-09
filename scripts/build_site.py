from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "slides.html"
STYLESHEET = "styles.css"


@dataclass
class DayPlan:
    number: int
    label: str
    theme: str
    summary: str
    images: list[str]
    captions: list[str]
    bullets: list[str]

    @property
    def filename(self) -> str:
        return f"day-{self.number}.html"


SUMMARIES = {
    1: "A soft landing day built around the Sheraton, a golden-hour walk through Ipanema, and sunset at Arpoador.",
    2: "A green, low-key Rio day with the botanical garden in the morning and the Lagoa shoreline in the afternoon.",
    3: "A wildlife-focused rainforest day in Tijuca with birds, monkeys, waterfalls, and a guided forest outing.",
    4: "The big water excursion: an early departure to Arraial do Cabo for beaches, caves, and clear-water snorkeling.",
    5: "Classic Rio views in the morning, one last beach block in the afternoon, and music in Lapa at night.",
    6: "A short farewell morning with sunrise, coffee, checkout, and the return flight back to Toronto.",
}


CAPTIONS = {
    1: ["Ipanema and Arpoador"],
    2: ["Jardim Botanico palms", "Lagoa shoreline"],
    3: ["Tijuca forest trail", "Cascatinha Taunay"],
    4: ["Arraial do Cabo coast", "Clear-water cove"],
    5: ["Sugarloaf panorama"],
    6: ["Final Rio sunrise"],
}


def extract_days(text: str) -> list[DayPlan]:
    blocks = re.findall(
        r"<!-- Day (\d+) -->(.*?)(?=(?:<!-- Day \d+ -->|</div>\s*<div class=\"scroll-hint\">))",
        text,
        re.S,
    )
    days: list[DayPlan] = []
    for raw_number, block in blocks:
        number = int(raw_number)
        label_match = re.search(r'<div class="day-label">(.*?)</div>', block, re.S)
        theme_match = re.search(r'<div class="day-theme">(.*?)</div>', block, re.S)
        image_matches = re.findall(r'<img class="[^"]+" src="([^"]+)"', block)
        bullet_matches = re.findall(r"<li>(.*?)</li>", block, re.S)
        if not label_match or not theme_match or not image_matches or not bullet_matches:
            raise ValueError(f"Could not parse day {number}")

        label = html.unescape(label_match.group(1).strip())
        theme = html.unescape(theme_match.group(1).strip())
        bullets = [html.unescape(re.sub(r"<.*?>", "", item).strip()) for item in bullet_matches]
        captions = CAPTIONS.get(number, [])
        if len(captions) < len(image_matches):
            captions = captions + [f"{theme} view {i}" for i in range(len(captions) + 1, len(image_matches) + 1)]

        days.append(
            DayPlan(
                number=number,
                label=label,
                theme=theme,
                summary=SUMMARIES[number],
                images=image_matches,
                captions=captions,
                bullets=bullets,
            )
        )
    return days


def nav_links(days: list[DayPlan], current: int | None = None) -> str:
    links = ['<a href="index.html" class="nav-home">Rio 2026</a>']
    for day in days:
        classes = "day-link"
        if current == day.number:
            classes += " active"
        links.append(f'<a href="{day.filename}" class="{classes}">Day {day.number}</a>')
    links.append('<a href="slides.html" class="nav-ghost">Original Slides</a>')
    return "\n".join(links)


def render_index(days: list[DayPlan]) -> str:
    cards = []
    for day in days:
        bullets = "".join(f"<li>{html.escape(item)}</li>" for item in day.bullets[:3])
        cards.append(
            f"""
      <article class="excursion-card reveal">
        <a class="card-media" href="{day.filename}">
          <img src="{html.escape(day.images[0])}" alt="{html.escape(day.theme)}">
        </a>
        <div class="card-copy">
          <div class="eyebrow">{html.escape(day.label)}</div>
          <h2><a href="{day.filename}">{html.escape(day.theme)}</a></h2>
          <p>{html.escape(day.summary)}</p>
          <ul class="preview-list">
            {bullets}
          </ul>
          <div class="card-meta">
            <span>{len(day.images)} gallery image{'s' if len(day.images) != 1 else ''}</span>
            <a href="{day.filename}">Open day page</a>
          </div>
        </div>
      </article>
"""
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Rio 2026 Excursions</title>
  <meta name="description" content="Rio 2026 excursion planner with one page per day and gallery views for each outing.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Playfair+Display:wght@600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{STYLESHEET}">
</head>
<body class="site-home">
  <header class="site-nav">
    <nav>
      {nav_links(days)}
    </nav>
  </header>

  <main>
    <section class="hero hero-home reveal">
      <div class="hero-copy">
        <div class="eyebrow">Rio de Janeiro · Apr 17-22, 2026</div>
        <h1>One page per day, with a gallery for every excursion.</h1>
        <p>
          This turns the original presentation into a small trip site: each day has its own page,
          focused itinerary, and image gallery, while the original slide deck stays available as a backup view.
        </p>
        <div class="hero-actions">
          <a href="{days[0].filename}" class="btn-primary">Start with Day 1</a>
          <a href="slides.html" class="btn-secondary">View original slides</a>
        </div>
      </div>
      <div class="hero-panel">
        <img src="{html.escape(days[3].images[0])}" alt="Arraial do Cabo coast">
      </div>
    </section>

    <section class="section-head reveal">
      <div class="eyebrow">Excursions</div>
      <h2>Daily itinerary pages</h2>
      <p>Each card opens a dedicated day page with the full plan and that day’s gallery.</p>
    </section>

    <section class="excursion-grid">
      {''.join(cards)}
    </section>
  </main>
</body>
</html>
"""


def render_day(days: list[DayPlan], day: DayPlan) -> str:
    gallery = []
    for image, caption in zip(day.images, day.captions):
        gallery.append(
            f"""
      <figure class="gallery-card reveal">
        <img src="{html.escape(image)}" alt="{html.escape(caption)}">
        <figcaption>{html.escape(caption)}</figcaption>
      </figure>
"""
        )

    bullet_items = "".join(f"<li>{html.escape(item)}</li>" for item in day.bullets)
    prev_link = f'<a href="day-{day.number - 1}.html" class="pager-link">Previous day</a>' if day.number > 1 else '<span></span>'
    next_link = f'<a href="day-{day.number + 1}.html" class="pager-link">Next day</a>' if day.number < len(days) else '<span></span>'

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(day.theme)} · Rio 2026</title>
  <meta name="description" content="{html.escape(day.summary)}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Playfair+Display:wght@600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{STYLESHEET}">
</head>
<body class="site-day">
  <header class="site-nav">
    <nav>
      {nav_links(days, current=day.number)}
    </nav>
  </header>

  <main>
    <section class="hero hero-day reveal">
      <div class="hero-copy">
        <div class="eyebrow">{html.escape(day.label)}</div>
        <h1>{html.escape(day.theme)}</h1>
        <p>{html.escape(day.summary)}</p>
        <div class="hero-actions">
          <a href="#gallery" class="btn-primary">Jump to gallery</a>
          <a href="#plan" class="btn-secondary">Read the plan</a>
        </div>
      </div>
      <div class="hero-panel">
        <img src="{html.escape(day.images[0])}" alt="{html.escape(day.theme)}">
      </div>
    </section>

    <section class="content-grid">
      <article class="detail-card reveal" id="plan">
        <div class="eyebrow">Daily plan</div>
        <h2>What happens on this day</h2>
        <ul class="detail-list">
          {bullet_items}
        </ul>
      </article>

      <aside class="detail-card reveal accent-card">
        <div class="eyebrow">Quick read</div>
        <h2>Why this day works</h2>
        <p>{html.escape(day.summary)}</p>
        <div class="stat-row">
          <span class="stat-label">Gallery</span>
          <strong>{len(day.images)} image{'s' if len(day.images) != 1 else ''}</strong>
        </div>
        <div class="stat-row">
          <span class="stat-label">Stops</span>
          <strong>{len(day.bullets)} highlights</strong>
        </div>
      </aside>
    </section>

    <section class="section-head reveal" id="gallery">
      <div class="eyebrow">Gallery</div>
      <h2>Images for {html.escape(day.theme)}</h2>
      <p>Self-contained images carried over from the original trip deck.</p>
    </section>

    <section class="gallery-grid">
      {''.join(gallery)}
    </section>

    <section class="pager">
      {prev_link}
      <a href="index.html" class="pager-link">All days</a>
      {next_link}
    </section>
  </main>
</body>
</html>
"""


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    days = extract_days(text)
    (ROOT / "index.html").write_text(render_index(days), encoding="utf-8")
    for day in days:
        (ROOT / day.filename).write_text(render_day(days, day), encoding="utf-8")


if __name__ == "__main__":
    main()
