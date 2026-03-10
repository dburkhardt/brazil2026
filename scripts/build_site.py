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

MIN_GALLERY_IMAGES = {
    1: 5,
    2: 4,
    3: 4,
    4: 5,
    5: 4,
    6: 4,
}

DAY_HOTEL_IMAGE_ORDER = {
    1: [0, 1, 2, 3],
    2: [1, 2, 0],
    3: [0, 3, 1],
    4: [2, 1],
    5: [2, 0, 1],
    6: [3, 0, 1],
}

DAY_ORIGINAL_CAPTION_EXCLUDES = {
    4: {"Arraial do Cabo coast", "Clear-water cove"},
}

DAY_FEATURED_IMAGES = {
    4: [
        (
            "https://commons.wikimedia.org/wiki/Special:FilePath/Vista_Arraial_do_Cabo.jpg",
            "Praia do Forno overlook",
        ),
        (
            "https://commons.wikimedia.org/wiki/Special:FilePath/Gruta_Arraial_do_Cabo.jpg",
            "Arraial sea cave",
        ),
        (
            "https://commons.wikimedia.org/wiki/Special:FilePath/Atlantic_ocean_view_Arraial_do_Cabo.JPG",
            "Atlantic coast in Arraial do Cabo",
        ),
        (
            "https://commons.wikimedia.org/wiki/Special:FilePath/Praia_do_Farol_-_Arraial_do_cabo.JPG",
            "Praia do Farol waters",
        ),
        (
            "https://commons.wikimedia.org/wiki/Special:FilePath/Prainha_Arraial_do_Cabo.jpg",
            "Prainha shoreline",
        ),
    ],
}


def extract_hotel_images(text: str) -> list[tuple[str, str]]:
    block_match = re.search(r'<div class="photo-grid">(.*?)</div>\s*<div class="bonvoy-strip">', text, re.S)
    if not block_match:
        return []

    return [
        (src, html.unescape(caption).strip())
        for src, caption in re.findall(
            r'<img src="([^"]+)" alt="[^"]+">\s*<div class="caption">(.*?)</div>',
            block_match.group(1),
            re.S,
        )
    ]


def merge_images(
    image_pairs: list[tuple[str, str]],
    extras: list[tuple[str, str]],
    minimum: int,
) -> tuple[list[str], list[str]]:
    merged: list[tuple[str, str]] = []
    seen: set[str] = set()

    for src, caption in [*image_pairs, *extras]:
        if src in seen:
            continue
        seen.add(src)
        merged.append((src, caption))

    if minimum > len(merged):
        minimum = len(merged)

    trimmed = merged[:minimum]
    return [src for src, _ in trimmed], [caption for _, caption in trimmed]


def extract_days(text: str) -> list[DayPlan]:
    hotel_images = extract_hotel_images(text)
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

        original_pairs = list(zip(image_matches, captions))
        excluded_captions = DAY_ORIGINAL_CAPTION_EXCLUDES.get(number, set())
        if excluded_captions:
            original_pairs = [(src, caption) for src, caption in original_pairs if caption not in excluded_captions]

        image_pairs = [*DAY_FEATURED_IMAGES.get(number, []), *original_pairs]
        extra_pairs: list[tuple[str, str]] = []
        for hotel_index in DAY_HOTEL_IMAGE_ORDER.get(number, []):
            if hotel_index < len(hotel_images):
                extra_pairs.append(hotel_images[hotel_index])
        images, captions = merge_images(
            image_pairs,
            extra_pairs,
            MIN_GALLERY_IMAGES.get(number, len(image_pairs)),
        )

        days.append(
            DayPlan(
                number=number,
                label=label,
                theme=theme,
                summary=SUMMARIES[number],
                images=images,
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
            <a href="{day.filename}">View day {day.number}</a>
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
  <title>Rio de Janeiro · April 2026</title>
  <meta name="description" content="Rio de Janeiro, April 17 to 22, 2026.">
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
        <h1>Rio, coast to forest.</h1>
        <p>Beach light, rainforest air, clear water in Arraial do Cabo, and slow evenings back in the city.</p>
        <div class="hero-actions">
          <a href="{days[0].filename}" class="btn-primary">Begin</a>
          <a href="#days" class="btn-secondary">Itinerary</a>
        </div>
      </div>
      <div class="hero-panel">
        <img src="{html.escape(days[3].images[0])}" alt="Arraial do Cabo coast">
      </div>
    </section>

    <section class="section-head reveal" id="days">
      <div class="eyebrow">April 17-22</div>
      <h2>Arrival to last light</h2>
      <p>Ipanema, Jardim Botanico, Tijuca, Arraial do Cabo, Sugarloaf, Lapa, and one last sunrise.</p>
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
  <title>{html.escape(day.theme)} · Rio de Janeiro</title>
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
          <a href="#plan" class="btn-primary">Plan</a>
          <a href="#gallery" class="btn-secondary">Gallery</a>
        </div>
      </div>
      <div class="hero-panel">
        <img src="{html.escape(day.images[0])}" alt="{html.escape(day.theme)}">
      </div>
    </section>

    <section class="content-grid">
      <article class="detail-card reveal" id="plan">
        <div class="eyebrow">Plan</div>
        <h2>Morning to night</h2>
        <ul class="detail-list">
          {bullet_items}
        </ul>
      </article>

      <aside class="detail-card reveal accent-card">
        <div class="eyebrow">Rhythm</div>
        <h2>{html.escape(day.label)}</h2>
        <p>{html.escape(day.summary)}</p>
        <div class="stat-row">
          <span class="stat-label">Scenes</span>
          <strong>{len(day.images)} scene{'s' if len(day.images) != 1 else ''}</strong>
        </div>
        <div class="stat-row">
          <span class="stat-label">Stops</span>
          <strong>{len(day.bullets)} highlights</strong>
        </div>
      </aside>
    </section>

    <section class="section-head reveal" id="gallery">
      <div class="eyebrow">{html.escape(day.label)}</div>
      <h2>{html.escape(day.theme)}</h2>
    </section>

    <section class="gallery-grid">
      {''.join(gallery)}
    </section>

    <section class="pager">
      {prev_link}
      <a href="index.html" class="pager-link">Rio</a>
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
