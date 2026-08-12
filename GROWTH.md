# Getting fashionhotspot in front of people who will click

Written 2026-08-12, against measurements of the live site rather than general
advice. Every number here came from checking, and where something is a guess it
says so.

---

## 1. The problem is not traffic yet. It is that most links do not pay you.

I mapped all 2,319 product links on the live homepage:

| Where the link sends people | Links | Share | Do you earn? |
| --- | ---: | ---: | --- |
| `s.click.aliexpress.com` | 864 | 37% | **Yes** — verified working |
| **`dealnews.com`** | **926** | **40%** | **No** |
| `amazon.com` | 189 | 8% | Not yet — application pending |
| `wesell.co.il` | 136 | 6% | Unknown |
| ksp, cal-store, tauclub, buyme, cpnclub, elal | ~145 | 6% | Unknown |

**Only 37% of your catalogue can pay you today.**

The AliExpress links are genuinely fine. I followed three of them and each
returned a 302 into `aliexpress.com` carrying `aff_fcid`, `aff_trace_key` and
`aff_platform`. That is a working affiliate relationship — money reaches you.

The 926 DealNews links are the problem, and they are worse than merely
unmonetised. DealNews is itself a deal aggregator that earns from outbound
clicks. Every visitor you send there converts into revenue **for DealNews**.
You are paying hosting to run someone else's affiliate funnel. Those links
arrived via an RSS feed — they still carry DealNews's own `?iref=rss-c142`
tracking parameter.

### Fix this before chasing traffic

Doubling visitors to a site where 55% of clicks pay nothing doubles the leak.
In rough order of value:

1. **Amazon approval converts a chunk of it.** Many DealNews listings *are*
   Amazon products. Once approved, resolve each DealNews URL to its underlying
   merchant and rewrite it with your `fashionhots0f-20` tag. That is the single
   biggest revenue change available.
2. **Drop what cannot be monetised.** A smaller catalogue that pays beats a
   large one that does not, and thin aggregated content is also what Amazon
   reviewers dislike.
3. **Check the Israeli merchants.** wesell, KSP, Cal-Store, TauClub, BuyMe and
   CPNClub are 320 links. Some run affiliate programmes; each one you join
   converts dead links into paid ones without adding a single visitor.

---

## 2. Where the traffic comes from, in the order worth doing it

### a. Search — the compounding one

You now have **35 guides across 6 languages: 210 pages, 221 URLs**, all with
`Article`, `ItemList` with `Product`/`AggregateOffer`, `BreadcrumbList` and
`FAQPage` structured data. That is a real SEO asset and it appreciates.

What is missing:

- **Submit the sitemap.** Google Search Console and Bing Webmaster Tools,
  `https://fashionhotspot.site/sitemap.xml`. Nothing happens until you do.
- **Internal linking.** The guides do not link to each other. A coffee guide
  that links to the kitchen guide keeps people on the site and tells Google the
  pages are related.
- **Six languages is a real edge.** Very few affiliate sites publish Hebrew,
  Greek and Portuguese. Competition in those languages is a fraction of
  English, so those pages will rank first. Watch which languages convert.

Expect nothing for 3–6 months. Search is slow and then it is not.

### b. The WhatsApp bot — the asset you already own

This is the strongest thing you have and it is currently switched off.

It scans 55+ Israeli Telegram deal channels, converts links to your affiliate
through a four-method fallback chain, price-checks before publishing, and posts
to WhatsApp groups. Groups convert far better than search traffic because the
audience already opted in and arrives warm.

To make it work again:

- It needs `GROQ_API_KEY` and `GEMINI_API_KEY` in `.env` — it currently crashes
  at startup without them, which is why it is not running.
- Fix the path bug first: `deals-core.js` writes `./queue.json` while
  `build-static.js` reads `workspace/skills/queue.json`. Deals found by the
  hunter never reach the website.

### c. Pinterest — genuinely underrated for this niche

Product images with prices are exactly what Pinterest surfaces, the posts keep
driving traffic for months rather than hours, and you now have **386 generated
images** sitting unused for distribution. One board per guide category.

### d. What not to bother with

- **Paid social pointing at AliExpress links is against their terms.** Do not.
- **Do not bid on "AliExpress" or "Amazon" in search ads.** Also against terms,
  and you would lose the auction anyway.
- Cold Facebook traffic to an affiliate page converts badly and burns money.

---

## 3. Coupons — you already have the machine, it needs feeding

`workspace/skills/coupons.json` holds 4 codes and `autoFetchCoupons()` refreshes
every 12 hours from the affiliate API and public promo pages.

Where more codes come from:

- **The AliExpress Portals affiliate dashboard** publishes seller coupons and
  platform-wide codes to affiliates. This is the legitimate source and the codes
  carry your attribution.
- **Seasonal events** — 11.11, Black Friday, Anniversary Sale — are where the
  volume is. Commission on Hot Products runs far above the base rate.
- **Store coupons per seller**, visible on the product page, can be surfaced
  next to each deal.

Two rules that matter: only publish codes you have verified still work, and keep
the affiliate disclosure visible on any page carrying them. A dead code costs
trust that took months to build.

---

## 4. Honest expectations

Affiliate sites do not go from nothing to significant in weeks. What decides it:

- **Content that answers a buying question.** Your guides do — they name a
  trade-off on every product and they say plainly that nothing was hands-on
  tested. That honesty is an asset; sites that fake testing get found out.
- **Monetised links.** Currently 37%. This is the fixable one.
- **A traffic source you own.** The WhatsApp groups, not rented attention.
- **Time.** Search compounds. Nothing else here does.

The realistic sequence: get Amazon approved → convert the DealNews links →
restart the WhatsApp bot → submit sitemaps → then think about volume.

---

## 5. The immediate checklist

- [ ] Submit `sitemap.xml` to Google Search Console and Bing
- [ ] Verify `contact@fashionhotspot.com` receives mail — **it has no MX records
      and Amazon will email you during review**
- [ ] After approval: rewrite the 926 DealNews links to their real merchants
- [ ] Add `GROQ_API_KEY` + `GEMINI_API_KEY`, fix the queue path, restart the bot
- [ ] Apply to the Israeli merchants' affiliate programmes
- [ ] Add internal links between related guides
- [ ] One Pinterest board per category using the 386 images already generated
