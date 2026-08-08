#!/usr/bin/env python
"""Replace the hero's emoji cubes with a real image, and fix the contact email.

The hero carried two CSS 3D cubes with emoji faces, a wireframe ring and three
coloured dots. They read as an early prototype and undercut the rest of the
site. They are replaced by one dark product still life composed for the hero's
plum-and-coral palette, with faded edges so it sits on the gradient instead of
looking pasted onto it. It keeps a data-depth attribute, so the existing
parallax handler animates it exactly as it animated the cubes.

Also swaps contact@fashionhotspot.com — a domain that does not exist, the site
is .site — for the real address.

Run against either the generator template or a built index.html:
    python tools/patch_hero.py <file> [<file> ...]
Idempotent.
"""
import re, sys
from pathlib import Path

OLD_EMAIL = "contact@fashionhotspot.com"
NEW_EMAIL = "fashionhotspotsite@gmail.com"

# The image is baked on a dark plum backdrop which is still lighter than the
# hero gradient, so without a mask its rectangle is clearly visible. The radial
# mask feathers the edges against whatever the hero is doing behind it; doing it
# in CSS rather than in the file means it can be tuned without regenerating.
CSS = """
.hero-visual{position:absolute;top:50%;right:3%;width:min(44vw,470px);transform:translateY(-50%);pointer-events:none;z-index:1;transition:translate .25s ease-out;-webkit-mask-image:radial-gradient(ellipse 62% 62% at 50% 48%,#000 55%,transparent 78%);mask-image:radial-gradient(ellipse 62% 62% at 50% 48%,#000 55%,transparent 78%)}
.hero-visual img{width:100%;height:auto;display:block;mix-blend-mode:lighten}
@media(max-width:980px){.hero-visual{display:none}}
@media(prefers-reduced-motion:reduce){.hero-visual{transition:none}}"""

VISUAL = """  <!-- hero visual (mouse parallax) -->
  <div class="hero-visual" data-depth="14">
    <img src="images/hero-home.webp" alt="" width="760" height="760" decoding="async" fetchpriority="high">
  </div>
"""

# Everything from the cubes comment up to (not including) the hero content.
CUBES_RE = re.compile(
    r"[ \t]*<!-- floating 3D cubes.*?-->.*?(?=<div class=\"hero-inner\">)",
    re.S)


def patch(path: Path) -> list:
    s = path.read_text(encoding="utf-8")
    orig = s
    done = []

    # --- 1. cubes -> image -------------------------------------------------
    if "hero-visual" not in s:
        s2, n = CUBES_RE.subn(VISUAL + "\n  ", s)
        if n:
            s = s2
            done.append(f"replaced hero cubes ({n})")

    # --- 2. css ------------------------------------------------------------
    if ".hero-visual{" not in s:
        m = re.search(r"^\.cube-wrap\{[^\n]*\n", s, re.M)
        if m:
            s = s[:m.end()] + CSS.strip("\n") + "\n" + s[m.end():]
            done.append("added hero-visual css")

    # --- 3. email ----------------------------------------------------------
    if OLD_EMAIL in s:
        n = s.count(OLD_EMAIL)
        s = s.replace(OLD_EMAIL, NEW_EMAIL)
        done.append(f"fixed {n} email reference(s)")

    if s != orig:
        path.write_text(s, encoding="utf-8")
    return done


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for f in sys.argv[1:]:
        p = Path(f)
        if not p.exists():
            print(f"{f}: MISSING")
            continue
        d = patch(p)
        print(f"{p.name}: {', '.join(d) if d else 'no change (already patched)'}")


if __name__ == "__main__":
    main()
