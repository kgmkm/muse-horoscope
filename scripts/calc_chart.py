#!/usr/bin/env python3
"""Horoscope calculation for the muse-horoscope skill.

Uses openephem (MIT) for calculation and ephemvis (MIT) for rendering.
Design rules (fixed by the project):
- Warnings are inspected here, never drawn on cards (cards use show_warnings=False).
- If the planet bodies come back empty (the classic DE440 failure), stop with an
  error instead of producing a pretty but empty chart.
- Asteroids are not used. Uranian (Trans-Neptunian) points are used.

Usage:
  python3 calc_chart.py natal --profile profile.json --out outdir
  python3 calc_chart.py daily --profile profile.json --date 2026-11-08 --out outdir

The DE440 kernel is found via --de440, $HOROSCOPE_DE440, ./kernels/de440.bsp,
or ~/.cache/muse-horoscope/de440.bsp. If missing, the script prints how to fetch it.
"""
import argparse, json, os, sys

BASE_BODIES = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
               "Uranus", "Neptune", "Pluto", "TrueNode", "MeanLilith"]
URANIAN_BODIES = ["Cupido", "Hades", "Zeus", "Kronos", "Apollon", "Admetos",
                  "Vulcanus", "Poseidon", "TransPluto"]
FAST_TRANSIT = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
PERSONAL_POINTS = ["Sun", "Moon", "ASC", "MC"]
HARD = {"square", "opposition"}
SOFT = {"trine", "sextile"}


def find_kernel(explicit=None):
    cands = [explicit, os.environ.get("HOROSCOPE_DE440"), "kernels/de440.bsp",
             os.path.expanduser("~/.cache/muse-horoscope/de440.bsp")]
    for c in cands:
        if c and os.path.exists(c):
            return c
    sys.exit("ERROR: de440.bsp not found. Fetch it once with:\n"
             "  mkdir -p ~/.cache/muse-horoscope && "
             "curl -L -o ~/.cache/muse-horoscope/de440.bsp "
             "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440.bsp\n"
             "or pass --de440 <path>.")


def clean(obj):
    return json.loads(json.dumps(obj, default=float))


def check_chart(chart, label):
    warnings = chart.get("warnings") or []
    real = [w for w in warnings if "asteroid" not in str(w).lower()]
    if real:
        print(f"[{label}] warnings: {real}", file=sys.stderr)
    if not chart.get("bodies"):
        sys.exit(f"ERROR: {label} chart has no bodies (DE440 problem?). Stopping.")


def load_profile(path):
    with open(path) as f:
        return json.load(f)


def moment_of(profile, date_s=None, time_s=None):
    from openephem import resolve
    if date_s is None:
        date_s, time_s = profile["birth_date"], profile["birth_time"]
    y, m, d = (int(x) for x in date_s.split("-"))
    hh, mm = (int(x) for x in time_s.split(":"))
    return resolve(date=(y, m, d), time=(hh, mm), lat=profile["lat"],
                   lon=profile["lon"], tz=profile.get("tz", "UTC"))


def natal_charts(profile, kernel):
    from openephem import assemble
    m = moment_of(profile)
    hs = profile.get("house_system", "Placidus")
    base = assemble(m, house_system=hs, bodies=BASE_BODIES, de440=kernel)
    full = assemble(m, house_system=hs, bodies=BASE_BODIES + URANIAN_BODIES, de440=kernel)
    check_chart(base, "natal")
    check_chart(full, "natal+uranian")
    return clean(base), clean(full)


def point_longitudes(chart):
    pts = {n: float(b["lon"]) for n, b in chart["bodies"].items()}
    ang = chart.get("angles") or {}
    for k in ("asc", "mc"):
        if k in ang:
            pts[k.upper()] = float(ang[k])
    return pts


def midpoint_contacts(chart, orb_max=1.5):
    """Bodies/points sitting on midpoints of personal-point pairs and of
    Sun/Moon. Returns list of dicts sorted by orb."""
    pts = point_longitudes(chart)
    anchors = [p for p in PERSONAL_POINTS if p in pts]
    best = {}
    names = list(pts)
    for i, a in enumerate(anchors):
        for b in anchors[i + 1:]:
            mid = ((pts[a] + pts[b]) / 2) % 360
            for c in names:
                if c in (a, b):
                    continue
                d1 = abs((pts[c] - mid + 180) % 360 - 180)
                d2 = abs((pts[c] - (mid + 180) % 360 + 180) % 360 - 180)
                diff = min(d1, d2)
                if diff <= orb_max:
                    key = (f"{a}/{b}", c)
                    if key not in best or diff < best[key]["orb"]:
                        best[key] = {"pair": key[0], "point": c, "orb": round(diff, 2)}
    return sorted(best.values(), key=lambda x: x["orb"])


def sorted_aspects(aspects, limit=None):
    s = sorted(aspects, key=lambda x: abs(float(x["orb"])))
    return s[:limit] if limit else s


def star_rating(cross, orb_max=3.0):
    """Simple deterministic rule: tight soft aspects raise, tight hard aspects
    lower. Result is 1..3 stars (never 0)."""
    score = 0.0
    for a in cross:
        orb = abs(float(a["orb"]))
        if orb > orb_max:
            continue
        w = orb_max - orb
        if a["aspect"] in SOFT:
            score += w
        elif a["aspect"] in HARD:
            score -= w
    if score >= 2.0:
        return 3
    if score >= -1.0:
        return 2
    return 1


def cmd_natal(args):
    from ephemvis import render_svg, render_aspect_grid_svg
    profile = load_profile(args.profile)
    kernel = find_kernel(args.de440)
    os.makedirs(args.out, exist_ok=True)
    base, full = natal_charts(profile, kernel)
    json.dump(base, open(f"{args.out}/natal.json", "w"), ensure_ascii=False, indent=1)
    json.dump(full, open(f"{args.out}/natal-uranian.json", "w"), ensure_ascii=False, indent=1)
    wheel = render_svg(base, theme="dark", title="", show_warnings=False)
    open(f"{args.out}/fig-natal-dark.svg", "w").write(wheel)
    grid = render_aspect_grid_svg(full, theme="dark", show_warnings=False) \
        if "show_warnings" in render_aspect_grid_svg.__code__.co_varnames \
        else render_aspect_grid_svg(full, theme="dark")
    open(f"{args.out}/fig-grid-dark.svg", "w").write(grid)
    summary = {
        "angles": base["angles"],
        "top_aspects": sorted_aspects(base["aspects"], 10),
        "top_aspects_uranian": sorted_aspects(
            [a for a in full["aspects"] if a["a"] in URANIAN_BODIES or a["b"] in URANIAN_BODIES], 10),
        "midpoint_contacts": midpoint_contacts(full),
    }
    json.dump(summary, open(f"{args.out}/natal-summary.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False, indent=1))


def cmd_daily(args):
    from openephem import assemble, cross_aspects
    from ephemvis import render_biwheel_svg
    profile = load_profile(args.profile)
    kernel = find_kernel(args.de440)
    os.makedirs(args.out, exist_ok=True)
    natal_file = args.natal or f"{args.out}/natal.json"
    if os.path.exists(natal_file):
        natal = json.load(open(natal_file))
        natal_u_file = natal_file.replace("natal.json", "natal-uranian.json")
        natal_u = json.load(open(natal_u_file)) if os.path.exists(natal_u_file) else natal
    else:
        natal, natal_u = natal_charts(profile, kernel)
        json.dump(natal, open(f"{args.out}/natal.json", "w"), ensure_ascii=False, indent=1)
        json.dump(natal_u, open(f"{args.out}/natal-uranian.json", "w"), ensure_ascii=False, indent=1)
    tm = moment_of(profile, args.date, args.time)
    transit = assemble(tm, house_system=profile.get("house_system", "Placidus"),
                       bodies=FAST_TRANSIT, de440=kernel)
    check_chart(transit, "transit")
    transit = clean(transit)
    json.dump(transit, open(f"{args.out}/transit-{args.date}.json", "w"), ensure_ascii=False, indent=1)
    cross = clean(cross_aspects(natal, transit))
    cross_u = clean(cross_aspects(natal_u, transit))
    deep = sorted_aspects([a for a in cross_u if a["a"] in URANIAN_BODIES], 3)
    bi = render_biwheel_svg(natal, transit, cross_aspects=cross, theme="dark",
                            title="", labels=("Natal", "Transit"), show_warnings=False) \
        if "show_warnings" in render_biwheel_svg.__code__.co_varnames \
        else render_biwheel_svg(natal, transit, cross_aspects=cross, theme="dark",
                                title="", labels=("Natal", "Transit"))
    open(f"{args.out}/fig-biwheel-dark.svg", "w").write(bi)
    summary = {
        "date": args.date,
        "rating_stars": star_rating(cross),
        "top_cross": sorted_aspects(cross, 8),
        "uranian_deep_dive_candidates": deep,
    }
    json.dump(summary, open(f"{args.out}/daily-summary-{args.date}.json", "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("natal", "daily"):
        p = sub.add_parser(name)
        p.add_argument("--profile", required=True)
        p.add_argument("--out", required=True)
        p.add_argument("--de440")
        if name == "daily":
            p.add_argument("--date", required=True, help="YYYY-MM-DD")
            p.add_argument("--time", default="07:00")
            p.add_argument("--natal")
    args = ap.parse_args()
    (cmd_natal if args.cmd == "natal" else cmd_daily)(args)


if __name__ == "__main__":
    main()
