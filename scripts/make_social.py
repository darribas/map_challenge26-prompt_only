"""Combine the three submission cards into one image for social media, with the site's address on it.

    python scripts/make_social.py

Reads figures/submission/{1,2,3}_*.png and writes figures/submission/social.png (3780 x 2000 px), laid out like the
site: prints slightly tilted on a light table, title above, link below.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CARDS = sorted((ROOT / "figures/submission").glob("[123]_*.png"))
OUT = ROOT / "figures/submission/social.png"
URL = "darribas.org/map_challenge26-prompt_only"

TABLE, INK, GREY = "#F1EFEA", "#2B2B2B", "#6E6E6E"
W, H = 3780, 2000
CARD_W, GAP, TOP = 1100, 135, 330
TILTS = (-1.6, 0.8, -0.6)


def font(name, size):
    return ImageFont.truetype(str(ROOT / "fonts" / name), size)


def centred(draw, y, text, fnt, fill):
    w = draw.textlength(text, font=fnt)
    draw.text(((W - w) / 2, y), text, font=fnt, fill=fill)


canvas = Image.new("RGB", (W, H), TABLE)
draw = ImageDraw.Draw(canvas)
centred(draw, 95, "Neighbours, near and far", font("Figtree-Bold.ttf", 120), INK)
centred(draw, 240, "#30DayMapChallenge · Day 10 · Prompting only", font("Figtree-Regular.ttf", 54), GREY)

for i, (path, tilt) in enumerate(zip(CARDS, TILTS)):
    card = Image.open(path).convert("RGBA")
    card = card.resize((CARD_W, round(card.height * CARD_W / card.width)), Image.LANCZOS)
    # a soft shadow under each print, as on the site
    pad = 60
    shadow = Image.new("RGBA", (card.width + 2 * pad, card.height + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle([pad, pad + 14, pad + card.width, pad + card.height + 14], fill=(0, 0, 0, 70))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    shadow.alpha_composite(card, (pad, pad))
    shadow = shadow.rotate(tilt, resample=Image.BICUBIC, expand=True)
    x = GAP + i * (CARD_W + GAP) + CARD_W // 2 - shadow.width // 2
    y = TOP + 20 + card.height // 2 - shadow.height // 2
    canvas.paste(shadow, (x, y), shadow)

centred(draw, H - 150, URL, font("SpecialElite-Regular.ttf", 64), INK)
canvas.save(OUT, optimize=True)
print(f"{OUT.relative_to(ROOT)} {canvas.size}")
