#!/usr/bin/env python
"""Generate candidate hero images for the homepage.

Replaces the floating emoji cubes, the wireframe ring and the coloured dots in
the hero — an early-prototype look that undercuts the rest of the site.

The homepage hero is dark plum with coral and amber accents, so these are
composed dark-on-dark with warm rim lighting and faded edges, to sit on the
gradient rather than look pasted onto it.

    python tools/hero_image.py            # generate the candidates
    python tools/hero_image.py --final N  # promote candidate N to hero-home.png
"""
import argparse, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from imagegen import generate, IMG  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

STYLE = ("Dark moody editorial product photograph on a near-black deep plum "
         "background, warm coral and amber rim lighting from the left, soft "
         "shadows, premium magazine styling, shallow depth of field, high "
         "detail, no text, no logos, no watermark, no people, no hands.")

CANDIDATES = {
    1: ("an elegant arrangement of premium shopping items floating and softly "
        "lit — wireless earbuds, a wristwatch, a small perfume bottle and a "
        "folded silk scarf — suspended at different heights"),
    2: ("a single stack of beautifully wrapped minimal gift boxes in deep plum "
        "and warm terracotta paper, softly lit from one side, arranged in a "
        "loose diagonal"),
    3: ("a curated flat arrangement of desirable objects on dark stone — a "
        "sleek watch, sunglasses, wireless earbuds and a leather card holder — "
        "shot from a low three-quarter angle with warm rim light"),
}


def fade_edges(path, feather=0.22):
    """Soft radial vignette to alpha, so the image melts into the gradient."""
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    inset_x, inset_y = int(w * feather), int(h * feather)
    d.ellipse([-inset_x, -inset_y, w + inset_x, h + inset_y], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(int(min(w, h) * 0.12)))
    im.putalpha(mask)
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", type=int)
    args = ap.parse_args()

    if args.final:
        src = IMG / f"hero-home-cand{args.final}.jpg"
        if not src.exists():
            sys.exit(f"{src} not found — generate candidates first")
        out = IMG / "hero-home.png"
        fade_edges(src).resize((760, 760), Image.LANCZOS).save(out, "PNG", optimize=True)
        print(f"promoted candidate {args.final} -> {out} ({out.stat().st_size // 1024}kb)")
        return

    for n, subject in CANDIDATES.items():
        out = IMG / f"hero-home-cand{n}.jpg"
        if out.exists():
            print(f"skip {out.name} (exists)")
            continue
        generate(f"{subject}. {STYLE}", out, (900, 900), quality=88)
        print(f"ok {out.name} ({out.stat().st_size // 1024}kb)")


if __name__ == "__main__":
    main()
