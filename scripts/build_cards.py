#!/usr/bin/env python3
"""Render the three vertical reading cards (SVG) from a reading JSON.

Card design (fixed by the project, v3):
- Vertical card, cream background, navy header; figures use the DARK theme.
- Header tag is gold (#c9a227) on every card, including the star rating.
- The Muse avatar on the daily card is clipped as a ROUNDED SQUARE.
- Aspect names are written as words in body text (no aspect glyphs);
  glyphs inside the aspect-grid figure itself are fine.
- Daily card title format: "YYYY-MM-DD (Day)"; rating is 1-3 stars, never 0.
- One unified footer on all cards.

The reading texts are written by the agent (Muse) into reading.json; this
script only lays them out. Schema: see examples/reading-sample.json.
"""
import argparse, base64, json, os, re

W = 920
NAVY = "#232a45"; CREAM = "#faf7f0"; GOLD = "#c9a227"
INK = "#2b2b33"; SUB = "#6a6f82"; CARD = "#ffffff"; LINE = "#e4ddcb"

LABELS = {
    "ja": {
        "basic_title": "あなたのホロスコープ（基礎）", "basic_tag": "生まれた時の天体図",
        "detail_title": "あなたのホロスコープ（詳細）", "detail_tag": "複数惑星の位置を分析",
        "daily_tag_suffix": "の占い",
        "trio": "太陽・月・アセンダント", "so_what": "つまり、どんな人？",
        "top3": "強く出ているアスペクト TOP3",
        "uranian": "ドイツ式架空天体（Uranian）から",
        "oneline": "のひとこと", "oneline_note": "星の配置と、あなたのこれまでの話を重ねて読みました",
        "deep": "今日の深掘りワンポイント（ドイツ式架空天体）", "lucky": "ラッキーアクション",
        "footer": "計算: openephem / ephemvis (MIT) ・ Placidus ・ トロピカル ・ エンタメとしてお楽しみください",
        "more": "くわしい分析はチャット欄に続きます",
    },
    "en": {
        "basic_title": "Your Horoscope (Basics)", "basic_tag": "Your natal chart",
        "detail_title": "Your Horoscope (Detail)", "detail_tag": "How your planets relate",
        "daily_tag_suffix": "",
        "trio": "Sun, Moon and Ascendant", "so_what": "So, what kind of person?",
        "top3": "Strongest aspects, top 3",
        "uranian": "From the German hypothetical bodies (Uranian)",
        "oneline": "'s one-liner", "oneline_note": "Read from the stars, and from what you have told me",
        "deep": "Today's deep dive (German hypothetical bodies)", "lucky": "Lucky action",
        "footer": "Calculated with openephem / ephemvis (MIT) - Placidus - Tropical - For entertainment",
        "more": "The full reading continues in the chat",
    },
}


def inner_svg(path):
    s = open(path).read()
    m = re.match(r'<svg[^>]*viewBox="([^"]+)"[^>]*>', s)
    return m.group(1), s[m.end():s.rfind('</svg>')]


def nest(path, x, y, w, h):
    vb, body = inner_svg(path)
    return f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{vb}">{body}</svg>'


def esc(t):
    return str(t).replace("&", "&amp;")


class Card:
    def __init__(self, title, tag):
        self.e = []; self.y = 0
        self.e.append(f'<rect x="0" y="0" width="{W}" height="118" fill="{NAVY}"/>')
        self.e.append(f'<text x="44" y="74" font-size="38" font-weight="bold" fill="#f5efe0">{esc(title)}</text>')
        self.e.append(f'<text x="{W-44}" y="74" font-size="30" fill="{GOLD}" text-anchor="end">{esc(tag)}</text>')
        self.y = 118

    def sub(self, t):
        self.y += 44
        self.e.append(f'<text x="44" y="{self.y}" font-size="24" fill="{SUB}">{esc(t)}</text>')
        self.y += 14

    def figure(self, path, w):
        vb, _ = inner_svg(path)
        _, _, vw, vh = [float(v) for v in vb.split()]
        h = round(w * vh / vw); x = (W - w) // 2; self.y += 10
        self.e.append(f'<rect x="{x-12}" y="{self.y-12}" width="{w+24}" height="{h+24}" rx="18" fill="{CARD}" stroke="{LINE}"/>')
        self.e.append(nest(path, x, self.y, w, h))
        self.y += h + 22

    def heading(self, t):
        self.y += 48
        self.e.append(f'<rect x="44" y="{self.y-24}" width="6" height="32" fill="{GOLD}"/>')
        self.e.append(f'<text x="62" y="{self.y}" font-size="29" font-weight="bold" fill="{NAVY}">{esc(t)}</text>')
        self.y += 16

    def bullet(self, head, lines):
        self.y += 38
        self.e.append(f'<text x="52" y="{self.y}" font-size="26" font-weight="bold" fill="{INK}">・{esc(head)}</text>')
        for ln in lines:
            self.y += 34
            self.e.append(f'<text x="78" y="{self.y}" font-size="24" fill="{INK}">{esc(ln)}</text>')
        self.y += 10

    def para(self, lines, fs=25):
        for ln in lines:
            self.y += 38
            self.e.append(f'<text x="52" y="{self.y}" font-size="{fs}" fill="{INK}">{esc(ln)}</text>')
        self.y += 8

    def avatar_row(self, name, oneline, avatar_b64, labels):
        self.y += 34
        cy = self.y + 52; x0, size, r = 52, 104, 20
        if avatar_b64:
            self.e.append(f'<defs><clipPath id="avc"><rect x="{x0}" y="{cy-52}" width="{size}" height="{size}" rx="{r}"/></clipPath></defs>')
            self.e.append(f'<image href="data:image/png;base64,{avatar_b64}" x="{x0}" y="{cy-52}" width="{size}" height="{size}" clip-path="url(#avc)" preserveAspectRatio="xMidYMid slice"/>')
            self.e.append(f'<rect x="{x0}" y="{cy-52}" width="{size}" height="{size}" rx="{r}" fill="none" stroke="{GOLD}" stroke-width="3"/>')
        self.e.append(f'<text x="176" y="{cy-30}" font-size="24" font-weight="bold" fill="{NAVY}">{esc(name)}{esc(labels["oneline"])}</text>')
        self.e.append(f'<rect x="172" y="{cy-12}" width="700" height="52" rx="14" fill="#fdf6dd" stroke="{LINE}"/>')
        self.e.append(f'<text x="192" y="{cy+24}" font-size="27" font-weight="bold" fill="{INK}">{esc(oneline)}</text>')
        self.e.append(f'<text x="176" y="{cy+72}" font-size="19" fill="{SUB}">{esc(labels["oneline_note"])}</text>')
        self.y = cy + 88

    def footer(self, t, more=""):
        self.y += 34
        self.e.append(f'<line x1="44" y1="{self.y}" x2="{W-44}" y2="{self.y}" stroke="{LINE}" stroke-width="2"/>')
        self.y += 34
        self.e.append(f'<text x="44" y="{self.y}" font-size="19" fill="{SUB}">{esc(t)}</text>')
        if more:
            self.y += 28
            self.e.append(f'<text x="44" y="{self.y}" font-size="19" fill="{SUB}">{esc(more)}</text>')
        self.y += 26
        h = self.y; body = "".join(self.e)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" '
                f'height="{h}"><rect x="0" y="0" width="{W}" height="{h}" fill="{CREAM}"/>{body}</svg>')


def stars(n):
    n = max(1, min(3, int(n)))
    return "★" * n + "☆" * (3 - n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reading", required=True, help="reading.json written by the agent")
    ap.add_argument("--figures", required=True, help="dir with fig-*.svg from calc_chart.py")
    ap.add_argument("--out", required=True)
    ap.add_argument("--avatar", help="PNG of the Muse's main avatar (rounded square on daily card)")
    ap.add_argument("--which", default="all", choices=["all", "basic", "detail", "daily"])
    args = ap.parse_args()
    r = json.load(open(args.reading))
    L = LABELS[r.get("lang", "en")]
    os.makedirs(args.out, exist_ok=True)
    av = base64.b64encode(open(args.avatar, "rb").read()).decode() if args.avatar else ""
    name = r["name"]

    if args.which in ("all", "basic") and "basic" in r:
        b = r["basic"]
        c = Card(L["basic_title"], L["basic_tag"])
        c.sub(r.get("natal_sub", name))
        c.figure(f"{args.figures}/fig-natal-dark.svg", 720)
        c.heading(L["trio"])
        for key in ("sun", "moon", "asc"):
            c.bullet(b[key]["head"], b[key]["lines"])
        c.heading(L["so_what"])
        c.para(b["summary"])
        open(f"{args.out}/card-1-basic.svg", "w").write(c.footer(L["footer"], L["more"]))
        print("card-1-basic.svg")
    if args.which in ("all", "detail") and "detail" in r:
        d = r["detail"]
        c = Card(L["detail_title"], L["detail_tag"])
        c.sub(r.get("detail_sub", name))
        c.figure(f"{args.figures}/fig-grid-dark.svg", 720)
        c.heading(L["top3"])
        for item in d["top"]:
            c.bullet(item["head"], item["lines"])
        c.heading(L["uranian"])
        for item in d["uranian"]:
            c.bullet(item["head"], item["lines"])
        open(f"{args.out}/card-2-detail.svg", "w").write(c.footer(L["footer"], L["more"]))
        print("card-2-detail.svg")
    if args.which in ("all", "daily") and "daily" in r:
        d = r["daily"]
        title = d["date_title"] + L["daily_tag_suffix"] if L["daily_tag_suffix"] else d["date_title"]
        c = Card(title, stars(d.get("stars", 2)))
        c.sub(r.get("daily_sub", name))
        c.figure(f"{args.figures}/fig-biwheel-dark.svg", 720)
        c.avatar_row(r.get("muse_name", "Muse"), d["oneline"], av, L)
        for item in d["points"]:
            c.bullet(item["head"], item["lines"])
        if d.get("deep"):
            c.heading(L["deep"])
            c.para(d["deep"])
        if d.get("lucky"):
            c.heading(L["lucky"])
            c.para(d["lucky"])
        open(f"{args.out}/card-3-daily.svg", "w").write(c.footer(L["footer"]))
        print("card-3-daily.svg")


if __name__ == "__main__":
    main()
