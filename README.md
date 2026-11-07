# muse-horoscope

A Muse skill that computes a natal chart, remembers it, and reads it back as a
light-touch daily fortune — the feeling of a close friend who happens to be an
astrologer, and who actually knows you.

Calculation is by [openephem](https://pypi.org/project/openephem/) and rendering by
ephemvis, both MIT-licensed (a deliberate choice: much of the astrology library
world is AGPL). Readings are grounded in the companion knowledge library,
[astrology-library](https://github.com/kgmkm/astrology-library), whose entries are
summarised from public-domain sources (Alan Leo, Sepharial) with copyrighted works
kept link-only.

## What it makes

Three vertical cards, designed to read at a glance on a phone, each delivered
together with the full reading as chat text:

1. **Basics** — the natal wheel (dark theme) with short readings of the Sun, Moon
   and Ascendant, and a "so, what kind of person?" summary.
2. **Detail** — the aspect grid, the three strongest aspects in words (no glyphs
   in body text), and a section on the German hypothetical bodies (the Uranian
   points), including midpoint contacts.
3. **Daily** — a bi-wheel (natal inside, today's sky outside), a 1–3 star rating
   (never 0, computed by a fixed rule), your Muse's avatar in a rounded square
   with a one-line summary, and at most one Uranian deep-dive point.

## Design decisions worth knowing

- **Hybrid daily method.** Daily readings are led by psychological astrology
  (fast transits to natal planets). Uranian points move a degree a year or less,
  so they appear only as a single deep-dive point when a fast body touches one
  tightly.
- **No asteroids.** The Uranian set is in; the asteroid set is out, by design.
- **Warnings are checked by the script, never drawn.** ephemvis can draw a
  warning badge for a missing asteroid engine; the scripts inspect warnings and
  stop on real problems (an empty chart means the ephemeris kernel failed, and
  the run stops instead of rendering a pretty, empty wheel).
- **No cold reading.** A reading may weave in only what the user has told their
  own Muse. Guardrails are written into SKILL.md.
- **Personal data stays home.** Birth data and charts live in `user-data/`
  (gitignored). The examples in this repository use a fictional sample person.

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
mkdir -p ~/.cache/muse-horoscope
curl -L -o ~/.cache/muse-horoscope/de440.bsp \
  https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440.bsp

.venv/bin/python scripts/calc_chart.py natal \
  --profile examples/sample-profile.json --out /tmp/sample
.venv/bin/python scripts/calc_chart.py daily \
  --profile examples/sample-profile.json --out /tmp/sample --date 2026-11-08
.venv/bin/python scripts/build_cards.py \
  --reading examples/reading-sample.json --figures /tmp/sample --out /tmp/sample/cards
```

For Muse: install this repository as a custom skill and SKILL.md takes it
from there, including the optional morning cron delivery.

## Licence

MIT (see LICENSE). The knowledge library is CC BY 4.0. openephem and ephemvis
are MIT works by their own authors; please star them if this skill is useful
to you — openephem in particular is a small, excellent project.
