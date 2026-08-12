#!/usr/bin/env python
"""Draft a new buying guide into content/<slug>.json.

    python tools/gen_guide.py --list                 # the queued categories
    python tools/gen_guide.py audio                  # one guide
    python tools/gen_guide.py --all                  # every missing one
    python tools/gen_guide.py audio --force          # overwrite an existing file

Writes English only. Images come from tools/imagegen.py afterwards and
translations from tools/translate.py, exactly as they do for the first twenty.

WHY A SCRIPT AND NOT JUST WRITING THEM

Twenty guides already exist and lint.py holds them to a real bar: ten products
each, 85+ words of body per product, at least one pro AND one con every time, a
price containing a digit, three or more FAQs, 800+ words total, and no claim of
hands-on testing anywhere. Fifteen more of those by hand is sixteen thousand
words that all have to clear the same gate. A script makes the bar an input
rather than something to remember.

THE HONESTY CONSTRAINT IS THE POINT

This site does not test products, and lint.py fails any copy that says
otherwise — "we tested", "in our tests", "tested picks" are all rejected, in
English and Hebrew. That is not a stylistic preference; it is the difference
between an editorial roundup and a lie. So the prompt below forbids invented
first-hand experience, demands a real drawback for every product, and asks for
prices as ranges because we do not hold live pricing.

Everything it writes is a claim someone could check. Nothing it writes is a
claim about us having used the thing.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

ROOT = Path(__file__).resolve().parent.parent
ENV = Path(r"C:\Users\AdBitRush\Documents\AdbitRush 22\2026\abri-brain\.env")
MODEL = os.environ.get("GUIDE_MODEL", "gemini-2.5-flash")
API = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent?key={}"

# The queue. Each entry is (slug, display category, brief) — the brief exists to
# stop fifteen guides converging on the same ten gadgets, and to keep each one
# clear of the twenty that already exist.
QUEUE = [
    ("audio", "Audio",
     "headphones, earbuds and speakers for home and commuting. NOT phone accessories "
     "(covered elsewhere) and NOT gaming headsets."),
    ("sleep", "Sleep",
     "things that measurably improve sleep: blackout, mattress toppers, pillows, white "
     "noise, bedside lighting. Be sceptical of sleep-tracking gadgets."),
    ("bathroom", "Bathroom",
     "storage, shower fittings, towels, mirrors, small fixes for a rented bathroom."),
    ("cleaning", "Cleaning",
     "vacuums, mops, microfibre, and the cleaning gadgets that are mostly marketing."),
    ("laundry", "Laundry",
     "drying, stain treatment, storage, steamers and garment care that extends how long "
     "clothes last."),
    ("baby", "Baby",
     "practical newborn-to-toddler gear. Nothing making safety claims we cannot support; "
     "point readers at the relevant safety standard instead."),
    ("cycling", "Cycling",
     "commuting by bike: locks, lights, tools, luggage, wet-weather kit. Not the bike."),
    ("running", "Running",
     "kit for people who run outdoors regularly. Not shoes, which need fitting in person "
     "and should be said so."),
    ("tools", "DIY tools",
     "the small toolkit that covers most household repairs, plus what is worth upgrading."),
    ("lighting", "Lighting",
     "lamps, bulbs, colour temperature and getting a rented room to stop feeling like an "
     "office."),
    ("security", "Home security",
     "cameras, sensors, locks. Be explicit about the privacy and subscription trade-offs."),
    ("air", "Air quality",
     "purifiers, humidifiers, monitors and what the numbers on them actually mean."),
    ("haircare", "Hair care",
     "dryers, brushes, heat protection and tools. Distinct from the beauty guide, which "
     "covers skin and make-up tools."),
    ("skincare", "Skincare",
     "the small number of ingredients with real evidence behind them, and the devices that "
     "mostly do not. No medical claims."),
    ("grilling", "Grilling",
     "barbecue and outdoor cooking: thermometers, tools, cleaning, fuel. Distinct from the "
     "kitchen guide."),
]


def api_key():
    if os.environ.get("GOOGLE_API_KEY"):
        return os.environ["GOOGLE_API_KEY"]
    for p in (ENV, Path("/root/repos/abri-brain/.env")):
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.startswith("GOOGLE_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no GOOGLE_API_KEY")


PROMPT = """Write a buying guide for a consumer shopping site, as JSON.

CATEGORY: {category}
BRIEF: {brief}

THE VOICE — this matters more than anything else below.
Direct, plainly written, sceptical. It tells the reader when something is not
worth buying. Every recommendation names its trade-off. It sounds like a person
who has thought about the category explaining it to a friend, not like
marketing copy. Short sentences are fine. Do not use exclamation marks. Do not
call anything "game-changing", "must-have", "revolutionary" or "the best".

HARD RULES — output violating any of these is unusable:
1. NEVER claim first-hand testing. Not "we tested", not "in our tests", not
   "we tried". We have not used these products. Write from what is publicly
   known about how the category works.
2. Every product needs at least one genuine drawback in "cons". A product with
   no real downside means you have not thought hard enough about it.
3. Prices are RANGES in US dollars, written like "$40-70". We do not hold live
   pricing. Never a single exact price.
4. No medical claims. No "cures", "clinically proven", "treats acne". Where
   evidence is weak, say it is weak.
5. Real products that exist and are widely available. Use the actual
   manufacturer and model name.
6. Each "body" is 130-170 words. THIS IS THE MOST COMMON FAILURE: drafts come
   back at 78-84 words and are rejected. 85 is a hard floor, not a target, and
   writing near it wastes a whole generation. Count as you go and overshoot.
   Say something specific — a mechanism, a number, a comparison, a named
   alternative — not vague praise. Specifics are what fill the words honestly.
7. Never use the word "cure", or "clinically proven", or "medical-grade", in
   any sentence, about any product. Not even to deny it. Say "may help with"
   or "there is limited evidence that" instead.

STRUCTURE:
- 10 products, ordered so the most useful comes first.
- "name": manufacturer and model, e.g. "Anker Soundcore Space Q45".
- "tag": five words or fewer naming the JOB this product does for a person, not
  a feature it has. No full stop. Write "The one to buy first", "For people who
  lose things", "If the room is cold". Do NOT write "Effective noise
  cancellation" or "Long battery life" — those are spec sheet lines, and the
  reader can already see the specs.
- "search": the phrase someone would type to find this exact product.
- "image": a short photographic description of the product on a plain surface,
  for an illustrator. No text, no logos, no people.
- "pros": 2-3 short concrete strings. "cons": 1-2, and they must be real.
- 4 FAQ entries answering what someone actually asks before buying, each answer
  60-110 words, at least one of which talks a reader OUT of something.
- "intro": 2 paragraphs, 60-90 words each, framing the category and its trap.
- "how_we_pick": 60-90 words on the selection criteria. It must state plainly
  that these are not hands-on reviews.
- "title": a specific, slightly dry sentence fragment with a point of view, in
  the style of these real examples from the same site:
    "The Home Coffee Setup, From First Upgrade to Last"
    "Kitchen Tools That Survive the Drawer Cull"
    "Camping Kit That Works in Bad Weather, Not Just Good"
    "Storage That Solves the Problem Instead of Moving It"
  Never "Best X of 2026", never "Buying Guide", never a colon followed by a
  list of the category's nouns.
- "dek": one sentence, under 160 characters.
- "hero_image": one photographic scene description of the category as a whole.

Return ONLY this JSON object:
{{"title":"","dek":"","intro":["",""],"how_we_pick":"","hero_image":"",
"products":[{{"name":"","tag":"","price":"","search":"","image":"","body":"",
"pros":[""],"cons":[""]}}],
"faq":[{{"q":"","a":""}}]}}"""


def post(model, body, tries=4):
    url = API.format(model, api_key())
    data = json.dumps(body).encode()
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read()[:300].decode('utf-8', 'replace')}"
            if e.code in (429, 500, 503):
                time.sleep(4 * (i + 1)); continue
            raise SystemExit(last)
        except Exception as e:  # noqa: BLE001
            last = str(e); time.sleep(3 * (i + 1))
    raise SystemExit(f"model call failed: {last}")


def generate(slug, category, brief):
    body = {
        "contents": [{"role": "user", "parts": [
            {"text": PROMPT.format(category=category, brief=brief)}]}],
        "generationConfig": {"temperature": 0.85, "responseMimeType": "application/json",
                             "maxOutputTokens": 32000},
    }
    data = post(MODEL, body)
    cand = (data.get("candidates") or [{}])[0]
    parts = (cand.get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise RuntimeError(f"empty response ({cand.get('finishReason')})")
    g = json.loads(text)

    g["slug"] = slug
    g["category"] = category
    g["updated"] = date.today().isoformat()
    words = (sum(len(p.get("body", "").split()) for p in g.get("products", []))
             + sum(len(x.split()) for x in g.get("intro", [])))
    g["read_minutes"] = max(4, round(words / 200))
    order = ["slug", "category", "title", "dek", "hero_image", "updated",
             "read_minutes", "intro", "how_we_pick", "products", "faq"]
    return {k: g[k] for k in order if k in g}


BANNED = re.compile(r"\bwe tested\b|\bwe tried\b|\bin our tests?\b|\btested picks\b|"
                    r"\bcures?\b|\bclinically proven\b|\bmedical[- ]grade\b", re.I)


def check(g):
    """The same bar lint.py enforces, applied before the file is written."""
    bad = []
    if len(g.get("products", [])) != 10:
        bad.append(f"{len(g.get('products', []))} products, need 10")
    if len(g.get("faq", [])) < 3:
        bad.append(f"{len(g.get('faq', []))} FAQs, need 3+")
    if len(g.get("intro", [])) != 2:
        bad.append(f"{len(g.get('intro', []))} intro paragraphs, need 2")
    for i, p in enumerate(g.get("products", []), 1):
        w = len(p.get("body", "").split())
        if w < 85:
            bad.append(f"p{i} body {w} words, need 85+")
        if not p.get("pros") or not p.get("cons"):
            bad.append(f"p{i} missing pros or cons")
        if not re.search(r"\d", str(p.get("price", ""))):
            bad.append(f"p{i} price has no number: {p.get('price')!r}")
        for k in ("name", "tag", "search", "image"):
            if not str(p.get(k, "")).strip():
                bad.append(f"p{i} empty {k}")
    blob = json.dumps(g, ensure_ascii=False)
    for m in set(BANNED.findall(blob)):
        bad.append(f"banned claim: {m!r}")
    total = (sum(len(p.get("body", "").split()) for p in g.get("products", []))
             + sum(len(x.split()) for x in g.get("intro", []))
             + len(g.get("how_we_pick", "").split()))
    if total < 800:
        bad.append(f"~{total} words, need 800+")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--retries", type=int, default=4,
                    help="regenerate this many times if the quality bar is missed")
    a = ap.parse_args()

    if a.list:
        for s, c, b in QUEUE:
            exists = "done" if (ROOT / "content" / f"{s}.json").exists() else "    "
            print(f"  {exists} {s:12} {c:14} {b[:60]}")
        return 0

    todo = [q for q in QUEUE if q[0] in a.slugs] if a.slugs else QUEUE
    if not a.slugs and not a.all:
        return print("pass slugs, --all, or --list") or 2
    if not a.force:
        todo = [q for q in todo if not (ROOT / "content" / f"{q[0]}.json").exists()]
    if not todo:
        return print("  nothing to do — all present (use --force to redo)") or 0

    ok = 0
    for slug, cat, brief in todo:
        for attempt in range(1, a.retries + 2):
            try:
                g = generate(slug, cat, brief)
            except Exception as e:  # noqa: BLE001
                # A truncated or malformed JSON body is a transient model
                # failure, not a reason to abandon the guide — this used to
                # `break` and lose the slug entirely on one bad response.
                print(f"  {slug:12} attempt {attempt}: generation failed — {e}")
                continue
            problems = check(g)
            if not problems:
                (ROOT / "content" / f"{slug}.json").write_text(
                    json.dumps(g, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                words = sum(len(p["body"].split()) for p in g["products"])
                print(f"  {slug:12} ok   {len(g['products'])} products, ~{words} words")
                ok += 1
                break
            print(f"  {slug:12} attempt {attempt}: {'; '.join(problems[:3])}")
        else:
            print(f"  {slug:12} GAVE UP after {a.retries + 1} attempts")
    print(f"\n  {ok}/{len(todo)} written")
    return 0 if ok == len(todo) else 1


if __name__ == "__main__":
    sys.exit(main())
