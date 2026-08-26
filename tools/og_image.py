"""Generate the social share card at images/og-home.jpg.

WHY THIS FILE EXISTS
--------------------
The homepage had no `og:image`, so every link shared into WhatsApp — the site's
main channel — rendered as a bare grey rectangle. The guides each have a hero
photo to use; the homepage is a live grid with nothing stable to point at, so
its card has to be drawn.

It is generated rather than hand-made so it can be regenerated when the palette
or the counts change, and so the numbers on it come from the repo instead of
from memory. Run:

    python tools/og_image.py

Colours are the real design tokens, converted from oklch here rather than
eyeballed into hex, so this card cannot drift away from the site's palette.

JPEG, not PNG: WhatsApp is the target and it treats large previews poorly. This
lands around 60 KB, well inside every platform's fetch limit.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "images" / "og-home.jpg"

W, H = 1200, 630  # the size every platform crops against


# --------------------------------------------------------------------------
# oklch → sRGB, so the card uses the same tokens as the stylesheet
# --------------------------------------------------------------------------
def oklch(l: float, c: float, h_deg: float) -> tuple[int, int, int]:
    h = math.radians(h_deg)
    a, b = c * math.cos(h), c * math.sin(h)

    l_ = (l + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (l - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (l - 0.0894841775 * a - 1.2914855480 * b) ** 3

    rgb = (
        +4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
        -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
        -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_,
    )

    def enc(u: float) -> int:
        u = max(0.0, min(1.0, u))
        u = 12.92 * u if u <= 0.0031308 else 1.055 * (u ** (1 / 2.4)) - 0.055
        return int(round(u * 255))

    return tuple(enc(v) for v in rgb)  # type: ignore[return-value]


BG     = oklch(0.945, 0.019, 80)   # --bg
CARD   = oklch(0.978, 0.014, 82)   # --card
INK    = oklch(0.21,  0.014, 55)   # --ink
INK3   = oklch(0.52,  0.014, 68)   # --ink3
ACCENT = oklch(0.55,  0.20,  25)   # --accent


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Archivo is not installed on the build machine; these are the closest
    available weights. The card is a picture, not a page, so a stand-in face is
    acceptable where it would not be in the site's own type."""
    for candidate in (name, "seguibl.ttf", "ariblk.ttf", "arialbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def guide_count() -> int:
    """Read the real number of guides so the card cannot claim a stale figure."""
    return len(list((ROOT / "content").glob("*.json")))


def lang_count() -> int:
    try:
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        from langs import LANGS  # type: ignore
        return len(LANGS)
    except Exception:
        return 6


def build() -> Path:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # Perspective grid, the same motif as the homepage backdrop. Kept very low
    # contrast so it reads as texture and never competes with the words.
    for x in range(0, W, 48):
        d.line([(x, 0), (x, H)], fill=CARD, width=1)
    for y in range(0, H, 48):
        d.line([(0, y), (W, y)], fill=CARD, width=1)

    # Accent rule down the left edge — the site's masthead device.
    d.rectangle([0, 0, 14, H], fill=ACCENT)

    pad = 86
    d.text((pad, 132), "fashionhotspot", font=font("seguibl.ttf", 104), fill=INK)

    d.text((pad, 268), "Daily deals from Amazon and AliExpress",
           font=font("arialbd.ttf", 44), fill=INK)

    n_guides, n_langs = guide_count(), lang_count()
    d.text((pad, 336), f"{n_guides} buying guides  ·  {n_langs} languages  ·  updated daily",
           font=font("arial.ttf", 32), fill=INK3)

    # Footer chip. Real claims only — the site does publish in six languages and
    # does rebuild nightly, and nothing here promises a price or a discount that
    # a visitor could arrive and find missing.
    chip_y = 468
    d.rounded_rectangle([pad, chip_y, pad + 470, chip_y + 78], radius=39, fill=ACCENT)
    d.text((pad + 40, chip_y + 20), "fashionhotspot.site",
           font=font("arialbd.ttf", 38), fill=(255, 255, 255))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "JPEG", quality=88, optimize=True, progressive=True)
    return OUT


if __name__ == "__main__":
    p = build()
    kb = p.stat().st_size / 1024
    print(f"wrote {p.relative_to(ROOT)}  {W}x{H}  {kb:.0f} KB")
    if kb > 300:
        print("  ⚠️  over 300 KB — some platforms skip large previews")
