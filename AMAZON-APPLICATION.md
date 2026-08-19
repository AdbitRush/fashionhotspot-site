# Amazon Associates — application readiness

**Prepared:** 2026-08-20 · **Site:** https://fashionhotspot.site
**Status in `site-config.json`:** `not_applied`

**Everything blocking has been fixed. The site is ready to submit.**
The two items marked ⚠️ below are yours to decide, not code.

---

## Apply here

**https://affiliate-program.amazon.com** → *Sign up* → follow the form.
Use the answers in "What the form asks" below.

The moment you submit, set the status so the repo does not lie about it:

```jsonc
// site-config.json
"amazon_associate_status": "pending",
```

---

## What was fixed to get here (2026-08-20)

| | Problem | Fixed |
|---|---|---|
| 1 | **17 links carried a stranger's Associates tag** — 15 on `mazion00-20`, 2 on `ranbd09-20`, inherited from the posts the products were harvested from. Reads as tag manipulation, and every click paid someone else. | `amazonOwnTag()` in `build-static.js` rewrites or appends `tag=` on every Amazon URL. Verified: 479 links, all `fashionhots0f-20`, zero foreign. |
| 2 | **481 products published price + image + star rating with no PA-API.** That content is PA-API-only under the Operating Agreement, and PA-API does not exist before approval — so the breach was visible on the exact page a reviewer reads. | `amazon_pa_content: false`. Amazon rows now show title + link only. Verified: 0 prices, 0 ratings, 0 Amazon-hosted images. Nothing deleted — see below. |
| 3 | Product titles in Hebrew on the English site (27% of cards) | 781 English titles recovered from the AliExpress API; now 10%. |
| 4 | Unreadable text — 5 surfaces between 1.17:1 and 2.20:1 | All above 4.5:1, most above 8:1. |
| 5 | Discounts on 96% of products, clustered at 52-57%, 546 of them exactly 2.00× | Non-credible ones dropped; now 63%, nothing above 70%. |

**Nothing was deleted in #2.** `archive.json` still holds all ~481 Amazon
products with verified images and prices. The flag withholds at *build* time.
The day `AMAZON_PAAPI_*` keys exist, `hasPaapi()` goes true, both gates open by
themselves, and one rebuild brings it all back.

---

## The requirements, and where we stand

| Requirement | Status |
|---|---|
| Substantial original content | ✅ **35 buying guides**, ~2,200 words each, × 6 languages = 210 pages. Written, not scraped. |
| Working, non-placeholder site | ✅ 1,462 live deals, every link checked, delisted products auto-dropped |
| Affiliate disclosure, clearly visible | ✅ Top banner **and** footer, in all six languages |
| Disclosure is truthful | ✅ *"We are not an Amazon Associate and earn nothing from Amazon links today."* True before, during and after review |
| Privacy policy | ✅ `privacy.html` — covers cookies, affiliate links, Amazon, personal data, contact |
| Contact route | ✅ `contact.html` + `fashionhotspotsite@gmail.com` |
| About page | ✅ `about.html` |
| Own Associates tag only | ✅ fixed today — all `fashionhots0f-20` |
| No PA-API content without PA-API | ✅ fixed today — withheld until keys exist |
| Not directed at children under 13 | ✅ general consumer goods |

---

## What the form asks, and how to answer

Answer plainly. Overstating traffic is the most common way to get refused, and
it is checkable.

| Field | Suggested answer |
|---|---|
| Website URL | `https://fashionhotspot.site` |
| What is your site about? | Curated daily deals on consumer goods — electronics, home, kitchen, fitness — plus 35 original buying guides in six languages. |
| Which topics best describe it? | Deals / Coupons · Consumer Electronics · Home |
| How do you drive traffic? | Organic search on the buying guides, plus a WhatsApp deals channel we operate. |
| How do you build links? | Manually and via the retailer affiliate APIs. |
| How do you monetise? | Affiliate commission only. No paid advertising on the site. |
| Monthly unique visitors | **Answer honestly.** If it is small, say so — a new site is not a reason for refusal, but an inflated number that does not match reality is. |
| Amazon Associates ID | `fashionhots0f-20` |

---

## ⚠️ Two things to decide — yours, not code

**1. Do you have a real traffic answer?** If the site has essentially no
visitors yet, applying still works, but Amazon closes accounts that make **no
qualifying sales within 180 days**. The WhatsApp channel is your strongest
answer here — it is a real audience you already own.

**2. AliExpress links sit on the same pages.** Amazon does *not* require
exclusivity, so this is allowed and is currently ON, earning. Only turn it off
if you would rather the guides lead with Amazon alone:
`python tools/site_toggle.py aliexpress off`.

---

## The day the acceptance email arrives

In this order. The first step is counter-intuitive, which is why it is first.

```jsonc
// site-config.json
"amazon_associate_status": "approved",
"amazon_pa_content": false     // <- LEAVE IT OFF
```

Scraped Product Advertising Content on a **live** Associates account is a
different order of risk from the same content on a site that has merely
applied. Before approval the worst case is a refusal you answer and resubmit.
After approval it is account closure, which is far harder to undo and takes the
commission with it.

Then:

1. **Request PA-API** from inside the Associates dashboard. It is a separate
   request and on current rules needs qualifying sales first — approval alone
   is not enough.
2. **Drop the keys in** `whatsapp-deals-bot/workspace/skills/config.js`
   (`AMAZON_PAAPI_ACCESS_KEY` / `SECRET_KEY` / `PARTNER_TAG`). Both gates open
   on their own. This was built as a key-drop; no code change needed.
3. **Update the disclosure** to the required wording — it must not say this
   before you are approved:
   > As an Amazon Associate I earn from qualifying purchases.

   Change `f_disc` and `annc` in `workspace/skills/i18n.json`, **all six
   languages**.
4. **Replace the snapshot with live PA-API data.** Prices must be refreshed or
   removed within 24 hours and carry their retrieval time. Retire
   `fetch-amazon-deals.js`, `merge-harvested-amazon.js`, `ingest-harvested.js`
   and `resolve-amazon-images.js` — all four scrape, and once PA-API works they
   are not merely unnecessary, they are the thing that can close the account.

### The one thing not to do

Do not re-enable scraped Amazon prices or images before PA-API keys exist,
whatever the site looks like in the meantime.
