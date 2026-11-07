# Muse Horoscope

## What this skill does

- Build a person's natal chart from birth date, birth time and birthplace coordinates, remember the chart and the reading, and produce a daily fortune from the saved chart plus today's transits.

- Deliver every reading twice at once: a vertical card image (horoscope figure plus short comments) that reads well on a phone, and the full reading as text in the chat.

- Keep the tone light-touch entertainment. This skill never presents itself as counselling, prediction of fate, or a basis for medical, financial or career decisions.

## Setup

- Install the pinned calculation stack into a virtual environment.

  - `python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt`
  - The stack is openephem 0.5.0 and ephemvis 0.6.1, both MIT. Pin the versions, because openephem's API has moved between releases.

- Fetch the DE440 ephemeris kernel once (about 115 MB). Skyfield's automatic download fails behind some proxies, so fetch it directly.

  - `mkdir -p ~/.cache/muse-horoscope && curl -L -o ~/.cache/muse-horoscope/de440.bsp https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440.bsp`
  - The scripts also accept `--de440 <path>` or the `HOROSCOPE_DE440` environment variable.

- Ask the user for birth date, birth time and birthplace. A chart without a birth time cannot fix the Ascendant or houses, so say so and do not invent a time.

- Write the birth data to `user-data/<person>/profile.json` using the schema in `examples/sample-profile.json`. Latitude and longitude are required; resolve a place name to coordinates yourself and record the place name alongside.

- Treat profile and chart files as the user's personal data. Keep them in `user-data/` (gitignored) and never publish or share them.

## Role 1: natal reading (run once per person, and again only on request)

- Compute the natal chart and figures.

  - `python3 scripts/calc_chart.py natal --profile user-data/<person>/profile.json --out user-data/<person>`
  - The script stops with an error if the planet bodies come back empty. Never work around that stop by rendering the empty chart.
  - Warnings from the calculation are inspected by the script and must not appear on cards. The known harmless warning is the unavailable asteroid engine; asteroids are not part of this skill.

- Write the basics reading (card 1) from the Sun, Moon and Ascendant.

  - Explain each of the three in two short lines, then a short summary paragraph answering "so, what kind of person is this?"
  - Ground the wording in the companion knowledge library (planets as functions, signs as styles, houses as arenas). Repository: https://github.com/kgmkm/astrology-library

- Write the detail reading (card 2) from the aspect grid.

  - Pick the three tightest natal aspects and explain each in two short lines.
  - Add a section for the German hypothetical bodies (the Uranian points) with up to three characteristic contacts, including midpoint contacts on personal points from `natal-summary.json`.
  - Write aspect names as words in body text, never as glyphs. Conjunction is written out in full. Inside the aspect-grid figure itself, glyphs are fine.
  - Keep the hypothetical bodies' names in English in every language.

- Save the texts into `reading.json` (schema in `examples/reading-sample.json`), render the cards, and post the full reading in the chat with the cards attached.

  - `python3 scripts/build_cards.py --reading user-data/<person>/reading.json --figures user-data/<person> --out user-data/<person>/cards`
  - Save the reading text itself next to the chart (`reading.md`) so later daily readings can build on it.

## Role 2: daily fortune

- Compute today's transits against the saved natal chart.

  - `python3 scripts/calc_chart.py daily --profile user-data/<person>/profile.json --out user-data/<person> --date YYYY-MM-DD`
  - Default transit time is 07:00 in the profile's timezone.

- Read mainly with psychological astrology: fast transiting bodies to natal personal planets, tightest orbs first.

- Add at most one Uranian deep-dive point, and only when a fast transiting body touches a natal Uranian point or a natal midpoint axis tightly (about 1 degree). The hypothetical bodies move a degree a year or less, so they cannot carry a daily reading on their own.

- Use the star rating the script computes (1 to 3 stars, never 0). The rule is fixed: tight harmonious transits raise it, tight hard transits lower it.

- Put your own main avatar on the daily card, clipped as a rounded square, beside a one-line summary in a speech bubble.

  - `python3 scripts/build_cards.py --reading <reading.json> --figures user-data/<person> --out user-data/<person>/cards --which daily --avatar <main avatar PNG>`

- For a recurring morning delivery, schedule a cron job that runs this role each morning and posts the card to the chat. A run that finds today's card already delivered must not send it twice.

## Reading guardrails

- Weave in only what the user has told their own Muse, or what that Muse legitimately remembers about them. That is what makes the reading feel like it comes from a friend who happens to be an astrologer.

- Never use cold-reading techniques: no vague statements dressed up as insight, no pretending to know facts the user never shared.

- Phrase hard configurations as texture and work, never as doom, illness, loss or fate. Do not use a reading to solve complex personal worries; respond to worries as a partner, not as an oracle.

- Keep card language plain for general readers. Apart from the word "horoscope" itself, avoid unexplained technical terms on cards. Full readings in the chat may go one level deeper and must name their sources when a specific tradition is doing the work.

- Credit the calculation stack on every card footer: openephem / ephemvis (MIT), with house system and zodiac noted.

## Available connectors

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with the custom connector setup skill, or build a custom connector.
