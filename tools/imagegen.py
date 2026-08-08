#!/usr/bin/env python
"""Generate hero + product imagery for fashionhotspot buying guides.

Same approach as the espresso repo's gen_images.py: Gemini image model, one
consistent house style so the whole site looks like a single publication.

    python tools/imagegen.py --test            # one image, check the key works
    python tools/imagegen.py                   # everything still missing
    python tools/imagegen.py coffee tech       # just these guides
"""
import argparse, base64, io, json, os, sys, time, urllib.error, urllib.request
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ENV = Path(r"C:\Users\AdBitRush\Documents\AdbitRush 22\2026\abri-brain\.env")
MODEL = "gemini-2.5-flash-image"
IMG = ROOT / "images"


def api_key():
    """Read the key without ever printing it."""
    if os.environ.get("GOOGLE_API_KEY"):
        return os.environ["GOOGLE_API_KEY"]
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            if line.startswith("GOOGLE_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no GOOGLE_API_KEY (env var or abri-brain/.env)")


# One house style for every image on the site, so 20 guides read as one brand.
STYLE = ("Clean editorial product photograph, soft diffused daylight, warm neutral "
         "background in cream and blush tones, subtle shadow, shallow depth of field, "
         "modern minimal magazine styling, high detail, no text, no logos, "
         "no watermark, no people, no hands.")

HERO_STYLE = ("Wide editorial lifestyle photograph, soft diffused daylight, warm cream "
              "and blush palette, modern minimal magazine styling, shallow depth of "
              "field, high detail, no text, no logos, no watermark, no faces.")


def _post(url, body, timeout=180):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def generate(prompt, out_path, size, quality=80):
    """Generate one image and write it to out_path. Returns the path."""
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}"
           f":generateContent?key={api_key()}")
    data = _post(url, {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    })
    for part in data["candidates"][0]["content"]["parts"]:
        d = part.get("inlineData") or part.get("inline_data")
        if d and d.get("data"):
            img = Image.open(io.BytesIO(base64.b64decode(d["data"]))).convert("RGB")
            img = _fit(img, size)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(out_path, "JPEG", quality=quality, optimize=True, progressive=True)
            return out_path
    raise RuntimeError("no image in response: " + json.dumps(data)[:300])


def _fit(img, size):
    """Center-crop to the target aspect ratio, then resize."""
    tw, th = size
    target = tw / th
    w, h = img.size
    if w / h > target:                      # too wide -> trim sides
        nw = int(h * target)
        box = ((w - nw) // 2, 0, (w + nw) // 2, h)
    else:                                   # too tall -> trim top/bottom
        nh = int(w / target)
        box = (0, (h - nh) // 2, w, (h + nh) // 2)
    return img.crop(box).resize((tw, th), Image.LANCZOS)


def run(jobs, retries=3):
    """jobs: list of (prompt, out_path, size). Skips anything already on disk."""
    todo = [j for j in jobs if not j[1].exists()]
    print(f"{len(jobs)} images, {len(jobs) - len(todo)} already present, {len(todo)} to make")
    ok = fail = 0
    t0 = time.time()
    for i, (prompt, out, size) in enumerate(todo, 1):
        for attempt in range(retries):
            try:
                generate(prompt, out, size)
                ok += 1
                print(f"[{i}/{len(todo)}] ok   {out.relative_to(ROOT)} "
                      f"({out.stat().st_size // 1024}kb)")
                break
            except Exception as e:
                msg = str(e)[:120]
                if attempt == retries - 1:
                    fail += 1
                    print(f"[{i}/{len(todo)}] FAIL {out.name}: {msg}")
                else:
                    time.sleep(2 + attempt * 3)
    dt = time.time() - t0
    print(f"\ndone: {ok} ok, {fail} failed, {dt:.0f}s")
    return fail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()

    if args.test:
        out = IMG / "_test.jpg"
        t0 = time.time()
        generate("a gooseneck pour-over kettle beside a bag of coffee beans. " + STYLE,
                 out, (600, 600))
        print(f"ok {out} {out.stat().st_size // 1024}kb in {time.time() - t0:.1f}s")
        return

    guides = {}
    for f in sorted((ROOT / "content").glob("*.json")):
        g = json.loads(f.read_text(encoding="utf-8"))
        guides[g["slug"]] = g
    if not guides:
        sys.exit("no content/*.json found")

    jobs = []
    slugs = args.slugs or list(guides)
    for slug in slugs:
        g = guides[slug]
        jobs.append((f"{g['hero_image']}. {HERO_STYLE}",
                     IMG / f"hero-{slug}.jpg", (1200, 630)))
        for i, p in enumerate(g["products"], 1):
            jobs.append((f"{p['image']}. {STYLE}",
                         IMG / f"{slug}-{i:02d}.jpg", (600, 600)))
    sys.exit(1 if run(jobs) else 0)


if __name__ == "__main__":
    main()
