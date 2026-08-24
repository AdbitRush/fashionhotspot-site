# Getting people in — the acquisition plan

Rewritten 2026-08-24 against measurements taken today. Supersedes the 2026-08-12
version, whose central finding (926 dead DealNews links) **has since been fixed** —
the live homepage now has zero.

Every number below came from checking the live site. Where something is an
estimate it says ESTIMATE.

---

## בעברית — התמצית

- **הבעיה היא לא התנועה. הבעיה היא שאי אפשר למדוד כלום** — אין שום אנליטיקס באתר.
- **קישור ששותפים בוואטסאפ לא מציג תמונה** — לדף הבית חסר `og:image`. זה הדבר
  הכי משתלם לתקן, והוא לוקח שעה.
- **אל תקנה תנועה לאתר.** העמלות מאליאקספרס נמוכות מדי — כל מבקר שווה אגורות.
- **כן כדאי לקנות הצטרפויות לקבוצת הוואטסאפ.** חבר בקבוצה שווה הרבה יותר
  ממבקר חד־פעמי, כי הוא חוזר כל חודש. זה הארביטראז' האמיתי כאן.
- הצינור החינמי שכבר בנוי ומחכה: **221 עמודים ב-6 שפות** + **Pinterest**.

---

## 1. Where you actually are

Measured on the live site today:

| Thing | State |
|---|---|
| Pages indexed-ready | **221 URLs**, 35 guides × 6 languages |
| Guide SEO | Article + ItemList/Product + Breadcrumb + FAQ schema, 7 hreflang tags, `og:image`, `twitter:card` — **all correct** |
| robots.txt + sitemap.xml | present, valid, 221 `<loc>` entries |
| Homepage speed | TTFB 0.31s, full load 0.83s — fine |
| Paying links | AliExpress **919** ✅ |
| Non-paying links | Amazon **479** (not approved yet), KSP 80, wesell 4 |
| WhatsApp group links on site | DealClaw ×3, findmydeal ×2 |
| **Analytics** | **none — no GA, no Plausible, no beacon, no external script at all** |
| **Homepage `og:image`** | **missing** (guides have it; the homepage does not) |
| **Guide → guide internal links** | **0** |
| `/he/` `/es/` `/fr/` `/de/` `/el/` | **403 Forbidden** (no index at the folder root) |
| Recorded visitor searches, all time | **1** (`air fryer`, English) |

That last row is the honest baseline: **traffic is effectively zero.** Nothing is
broken about that — the site was finished days ago and has never been promoted.
It does mean nobody should be judging conversion rates yet.

---

## 2. The one strategic decision

You are a media buyer, so the instinct is to buy traffic. **Don't — not to the site.**

The arithmetic, using AliExpress's real commission band (3–9%) and a typical
basket:

```
avg order            ~$15
commission @ 5%      ~$0.75  per completed order
site→merchant CTR    ~15%    ESTIMATE
merchant conversion  ~3%     ESTIMATE
                     ────────
value per visitor    ~$0.003   (0.15 × 0.03 × 0.75)
```

Cheapest realistic click in Israel is ₪0.30+. You would be paying roughly
**30–100× what a visitor returns.** No creative fixes a gap that size.

**But a group member is not a visitor.** A member sees deals every day for
months, and the cost to reach them again is zero:

```
member clicks ~2 deals/month × $0.30 avg     = $0.60/mo   ESTIMATE
12-month retention                            ≈ $7 lifetime  ESTIMATE
cost per group join (click-to-join campaign)  ₪0.50–2.00     ESTIMATE — must be tested
```

That one **can** be positive, and it is the arbitrage your skills actually fit:

> **Buy group joins. Never buy pageviews.**
> Optimise for cost-per-join, and treat the site as the thing that converts and
> retains, not the thing you advertise.

Everything below is ordered so the free compounding channels run while you test
that number with a small budget.

---

## 3. Phase 0 — Instrument first (nothing else until this is done)

You cannot run acquisition blind, and right now the site records **nothing**.
Every dollar spent before this is unattributable.

1. **Site analytics — cookieless.**
   Recommendation: **Cloudflare Web Analytics** — free, one script tag, no
   cookies, so **no consent banner needed**. That matters because you publish in
   German, French, Spanish and Greek: GDPR applies to those visitors, and GA4
   would force a cookie banner onto every page.
   *Alternative if you want to own the data: self-host **Umami** on the VPS you
   already run — free, same cookieless property, one more service to maintain.*

2. **Outbound click tracking — build it, don't buy it.**
   The revenue event is *leaving toward a merchant*, and no third party sees that
   cleanly. A small `api/click.php` — same anonymous design as the existing
   `searches.php`: destination, category, language, count. No IP, no session.
   Then you can finally answer *which categories actually earn*.

3. **Google Search Console + Bing Webmaster Tools.** Submit
   `https://fashionhotspot.site/sitemap.xml` to both. **Until you do this, the
   221 pages may never be crawled.** This is the single highest-value 10 minutes
   on the whole list, and only you can do it — it needs your Google account.

4. **Amazon Associates: submit the application.** 479 links currently pay
   nothing. That is ~34% of the catalogue working for free. Traffic growth
   multiplies that leak, so fix it *before* the traffic, not after.

---

## 4. Phase 1 — Make every shared link render (highest ROI per hour)

Your primary channel is WhatsApp. **A link shared in WhatsApp today shows a bare
grey rectangle**, because the homepage has no `og:image`. Guides have one; the
page people actually paste does not.

- [ ] Add `og:image` (1200×630), `og:image:width/height`, `twitter:card`,
      `og:locale` to the homepage and every language homepage.
- [ ] **Put the OG tags at the very top of `<head>`.** WhatsApp's crawler reads
      only the first chunk of a page — and your homepage HTML is **2.1 MB**. Tags
      that sit late in the document can be missed entirely.
- [ ] Add a **share button on every deal card** (`wa.me/?text=` + `navigator.share`
      on mobile). There is currently **no share affordance anywhere on the site**.
      This is the cheapest possible distribution: it turns each visitor into a
      channel, and it costs one button.
- [ ] Fix the **403 at `/he/`, `/es/`, `/fr/`, `/de/`, `/el/`** — a Hebrew visitor
      who types the folder gets *Forbidden*. Each needs an index page listing that
      language's guides.

**Expected effect:** WhatsApp shares stop looking broken. On a channel that is
100% link-sharing, preview cards are typically a large multiplier on click-through
— this is the difference between a share that works and one that is ignored.

---

## 5. Phase 2 — Close the WhatsApp loop (the asset you already own)

The bot scans 55+ Israeli Telegram deal channels, rewrites links to your
affiliate, price-checks, and publishes. It is the strongest thing you have.

**The loop is broken in one place:** the deals the bot posts **do not contain a
link back to the site.** The group is a dead end — members never become visitors,
so they never see the guides, the search, or the other 220 pages.

- [ ] **Append a short site link to every posted deal.** One line. Turns a
      one-way feed into a loop.
- [ ] **Post the guides to the group**, not only deals — one guide a day rotating
      through the 35. It is content you already own and have never distributed.
- [ ] **Seed the groups where deal-hunters already are:** Israeli Facebook deal
      groups, Telegram deal channels, Reddit (`r/Israel`, `r/aliexpress`), student
      and neighbourhood groups. Post *value first* — a genuinely good deal — with
      the group link second. Straight link-drops get removed.
- [ ] **Give people a reason the other groups don't have:** *findmydeal* is
      genuinely differentiated — you type any product and get live results back.
      No competing group does that. Lead with it.

---

## 6. Phase 3 — Pinterest (free, compounding, already planned)

`PINTEREST.md` in this repo is a finished 229-line plan with real pin titles,
descriptions, boards and image paths, generated from `content/*.json`. **It has
never been executed.**

Pinterest is a search engine, not a feed: pins keep returning traffic for years,
the audience is in a buying mindset, and every guide already has a hero image.

Do first: claim the domain (Settings → Claimed accounts). Then 2–5 pins a day,
destination = the **guide URL, never a raw affiliate link** (Pinterest restricts
those; the guide is where your links live anyway).

Needs your account, so only you can start it — the work is already written.

---

## 7. Phase 4 — SEO compounding (slow, then sudden)

The technical foundation is genuinely good. Three gaps:

- [ ] **Internal linking: currently 0 guide→guide links.** 221 pages that never
      reference each other waste their own link equity and give a visitor no
      second page. A "related guides" row at the foot of each guide is a
      `build.py` change and lifts both rankings and pages-per-visit.
- [ ] **Turn the search log into content.** `api/searches.php` records what people
      asked for and how many results they saw. Terms with high counts and **0**
      results are a list of guides to write, sourced from real demand.
- [ ] **Six languages is a real edge.** Almost no affiliate site publishes Hebrew,
      Greek and Portuguese. Competition there is a fraction of English, so those
      pages will rank first — watch which language converts and write for it.

Expect nothing for 3–6 months. Then it compounds and never asks for budget again.

---

## 8. Phase 5 — Paid, and only in the form that works

Run this **only after Phase 0 is measuring**, and only as *cost-per-join*.

- **Click-to-WhatsApp / traffic-to-invite-link campaigns, Meta, Israel.**
  Small test budget (₪300–500) purely to establish the real cost per join.
  Kill it if a join costs more than ~₪3.
- **Do not run Google Ads to guide pages** without reading the *thin affiliate /
  bridge page* policy first. Your guides do carry original comparison content,
  which is the thing that policy asks for — but the account risk is real and an
  affiliate account ban is hard to reverse.
- **Judge on cost-per-join, then retention** — how many are still in the group at
  day 30. A cheap join that leaves in a week is worth nothing.

---

## 9. Split of the work

**Only you can do these** (they need your accounts):

1. Google Search Console + Bing — submit the sitemap ← *do this first, it is free and it is 10 minutes*
2. Amazon Associates — submit the application
3. Pinterest — claim domain, start pinning from `PINTEREST.md`
4. Seed the groups in the communities you're already in
5. Approve any ad budget

**I can ship these on your say-so:**

1. Analytics + `api/click.php` outbound tracking
2. Homepage `og:image` / `twitter:card` / `og:locale`, tags moved to the top of `<head>`
3. Share buttons on deal cards
4. Language index pages — fixes the five 403s
5. Site link appended to every deal the bot posts
6. Related-guides internal linking in `build.py`

---

## 10. What to check, and when

| When | Question | Where the answer is |
|---|---|---|
| Day 7 | Are the 221 pages being crawled? | Search Console → Coverage |
| Day 7 | Does a shared link show a picture? | Paste it into a WhatsApp chat |
| Day 30 | Which category earns? | `api/click.php` log |
| Day 30 | What are people asking for that you don't have? | `api/searches.php?only=missing` |
| Day 30 | What does a group join cost? | Ad platform ÷ actual joins |
| Day 90 | Is search traffic moving at all? | Search Console → impressions curve |

**The first three lines of this document's plan — analytics, sitemap submission,
and `og:image` — are worth more than any amount of ad spend made before them.**
