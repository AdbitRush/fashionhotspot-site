# fashionhotspot — HANDOFF

**עודכן:** 2026-08-10
**אתר חי:** https://fashionhotspot.site
**ריפו:** https://github.com/AdbitRush/fashionhotspot-site

---

## ⚠️ הריפו הזה נוצר אוטומטית — אל תערכו כאן

`index.html` וקבצי האתר **נבנים** ע"י `build-static.js` בריפו
[whatsapp-deals-bot](https://github.com/AdbitRush/whatsapp-deals-bot)
ונדחפים לכאן אוטומטית. עריכה ישירה כאן תימחק בבנייה הבאה.

| מה לערוך | איפה |
|----------|------|
| עיצוב, פריסה, CSS, קרוסלה, צ'יפים | `whatsapp-deals-bot/site-template.js` |
| לוגיקת דילים, סינון, תמונות | `whatsapp-deals-bot/build-static.js` |
| תרגומים (6 שפות) | `whatsapp-deals-bot/workspace/skills/i18n.json` |
| **המדריכים** (20 מאמרים × 6 שפות) | `fashionhotspot-site/content/` ← **כן נערך כאן** |
| מתגי affiliate | `fashionhotspot-site/site-config.json` ← **כן נערך כאן** |

### הזרימה המלאה
```
whatsapp-deals-bot: node build-static.js     # בונה docs/ ומסנכרן לריפו הזה
/root/bin/fashionhotspot-pull.sh             # מושך את הריפו הזה על ה-VPS
fashionhotspot-site: bash deploy.sh          # מעלה ב-FTP ל-fashionhotspot.site
```
`deploy.sh` עולה על כל העץ (366 קבצים). בעבר הוא העלה 7 קבצים קשיחים בלבד —
אם משהו "לא מתעדכן באתר", זו הייתה הסיבה ההיסטורית.

---

## סטטוס נוכחי

| | |
|--|--|
| דילים בעמוד הראשי | **1206** — אמזון 215 · AliExpress 815 · ישראל 176 |
| צ'יפים | All / AliExpress / Amazon / Israel — סינון בצד הלקוח, עובד |
| מדריכים | 20 מאמרים × 6 שפות (en/he/es/fr/de/el) = 120 עמודים |
| מדריכים — affiliate | **אמזון בלבד** (0 קישורי AliExpress, 10 כפתורי קנייה לעמוד) |
| תמונות | 992 מתוך 1206 עם תצלום אמיתי; 214 מציגים אריח קטגוריה |
| מובייל 375px / 428px | אין גלילה אופקית, אזורי מגע 44px |

### שני מפתחות שונים ב-`site-config.json` — לא לבלבל
```jsonc
{
  "affiliates": { "amazon": true, "aliexpress": false, "israel": true },
  // ↑ שולט על *המדריכים* בלבד
  // "feed": { ... }  ← אם קיים, מצמצם את *העמוד הראשי*. אם חסר — הכל מתפרסם.
}
```
בעבר שניהם היו אותו מפתח, ולכן מעבר ל"אמזון בלבד" במדריכים מחק 815 דילים
מהעמוד הראשי כתופעת לוואי. הופרדו במכוון.

---

## המצב מול אמזון — נכון ל-2026-08-14

**עדיין לא הוגשה בקשה.** הקובץ `site-config.json` אמר `"pending"` והאתר הכריז
"We have applied to the Amazon Associates Program" — שניהם היו לא נכונים ותוקנו.
הסטטוס עכשיו `not_applied`.

The site is deliberately arranged so that nothing on it needs to be taken down
when you apply. Two rules produced that arrangement, and both are worth
understanding before changing anything:

1. **Product Advertising Content — price, list price, star rating, review count
   and the product image — may only be displayed if it came from PA-API.**
   PA-API exists only after approval. So none of it can be shown legitimately
   before then, no matter where it was obtained.
2. **Amazon's Conditions of Use forbid scraping.** Search pages already refuse
   plain HTTP (2.3KB stub, zero results) and product pages started returning
   CAPTCHAs after ~450 automated fetches from one IP in an afternoon.

| Surface | What it shows today | Why |
|---|---|---|
| Homepage grid | 839 deals, AliExpress + Israel only. Every row has a real photo AND a price. Zero placeholders. | Amazon rows are filtered out by `feed.amazon: false`. A compliant Amazon card can show no price, no rating and no photo, and 482 blank cards is a worse shop than 839 complete ones. |
| Amazon platform chip | hidden automatically | A chip that filters to an empty grid is worse than no chip. It reappears on its own when `feed.amazon` goes true. |
| 35 buying guides | ~2,200 words each × 6 languages, 10 `amazon.com/s?k=` search links per guide, no prices, no images | This is the compliant shape, and it is the part of the site a reviewer actually reads. Search links are permitted without PA-API. |
| Disclosure | "We are not an Amazon Associate and earn nothing from Amazon links today." | True before, during and after an application — needs no edit on the day you submit. |

**What is stored but not shown:** `archive.json` holds ~482 Amazon products with
verified images (`resolve-amazon-images.js` checked every URL returns ≥300px)
and prices. Nothing was deleted. The gates in `build-static.js` — `amazonSafeImage()`
and `amazonSafeFacts()` — withhold them at build time only.

---

## After acceptance — the order to do things in

The acceptance email is not the finish line; Amazon closes accounts that make no
qualifying sales. Do these in order.

### 1. On the day the email arrives (10 minutes)

```bash
# fashionhotspot-site/site-config.json
"amazon_associate_status": "approved"
"feed": { "amazon": true, ... }        # Amazon returns to the homepage grid
```

Do **not** add prices or images yet — `feed: true` alone brings the cards back
with titles and buy buttons. They will look thin until step 2, which is correct.

### 2. Request PA-API, then add the keys (this is the unlock)

PA-API is a separate request from inside the Associates dashboard, and on
current rules it needs qualifying sales before it is granted — approval alone is
not enough. Once you have credentials:

```js
// whatsapp-deals-bot/workspace/skills/config.js
AMAZON_PAAPI_ACCESS_KEY: '...',
AMAZON_PAAPI_SECRET_KEY: '...',
AMAZON_PAAPI_PARTNER_TAG: 'fashionhots0f-20',
```

`hasPaapi()` goes true and **both gates open by themselves**. The ~482 stored
Amazon products come back with photographs and prices in one rebuild. No code
change is needed — this was built to be a key-drop.

### 3. Replace the snapshot with live PA-API data (the real work)

This is the step that is easy to skip and shouldn't be. Right now Amazon prices
in `archive.json` are a scrape-time snapshot. PA-API terms require prices to be
refreshed or removed **within 24 hours**, and to carry the time they were
retrieved.

- Write `workspace/skills/amazon-paapi.js` against `GetItems` and have
  `build-static.js` read prices from it instead of from `archive.json`.
- Retire `fetch-amazon-deals.js`, `merge-harvested-amazon.js`,
  `ingest-harvested.js` and `resolve-amazon-images.js`. All four scrape. Once
  PA-API works they are not just unnecessary, they are the thing that can get
  the account closed.
- Delete the "verify price" note on cards once prices are live and timestamped —
  it exists because the numbers are stale, and it stops being honest-sounding
  and starts being an admission.

### 4. Then, and only then, grow the site

| Do | Why it matters more after approval than before |
|---|---|
| Turn AliExpress back on in the guides (`python tools/site_toggle.py aliexpress on`) | It was switched off for a review that was never happening. Amazon does not require exclusivity. |
| Write guides for the categories that have none | Guides convert far better than a grid, and they are the only pages that rank. Missing: garden, tools, jewelry — the same three the homepage auto-hides for having under 10 deals. |
| Add real editorial to category pages | A category page with a paragraph of judgement outranks a wall of cards. |
| Self-host Israeli thumbnails | ksp.co.il caps at 300px; see "מה נשאר" below. |
| Full visual redesign | Deliberately deferred until after approval — do not spend the effort on a site that might need to change shape. |

### The one thing not to do

Do not re-enable scraped Amazon prices or images before PA-API keys exist,
whatever the site looks like in the meantime. That combination — scraped Product
Advertising Content on a live Associates account — is the fastest route from
"approved" back to "closed", and it is much harder to recover from than waiting.

---

## מה נשאר

| נושא | סטטוס |
|------|--------|
| **~482 מוצרי אמזון מאוחסנים ולא מוצגים** | לא באג ולא חוסר — ראו "After acceptance" למעלה. התמונות כבר אומתו (`resolve-amazon-images.js`, כל URL מחזיר ≥300px) והמחירים שמורים ב-`archive.json`. שתי השערים ב-`build-static.js` מחזיקים אותם עד שיהיו מפתחות `AMAZON_PAAPI_*`. השורה הישנה כאן דיברה על 209 כרטיסים "בלי תמונה" — זה כבר לא המצב |
| ~60 תמונות ישראליות ב-200-349px | ksp.co.il מפרסם 300px בלבד (`/big/` ו-`/large/` מחזירים פיקסל 1x1), buyme משתנה בלי תבנית. פתרון: אחסון עצמי של תמונות ממוזערות |
| 2 קישורי תמונה מתים | rami-levy 404, max.co.il מפנה לעמוד שגיאה — נופלים לאריח אוטומטית |
| עיצוב מחדש מלא | נדחה במכוון עד אחרי אישור אמזון. שלושת מעברי הליטוש כבר בוצעו |
| סיסמת FTP | **להחליף** — נחשפה בפלט `curl -v` ישן. למחוק גם `.env.ftp.bak` מה-VPS |

---

## מלכודות שכבר נפלנו בהן

1. **`placeholderFor` היא פונקציית build-time.** היא לא קיימת בדפדפן. שימוש בה
   בקוד שרץ בצד הלקוח זורק ReferenceError. בצד הלקוח יש `IMG_FALLBACK`.
2. **גרשים בתוך data-URI של SVG.** אם ה-URI מוטמע ב-`onerror="this.src='...'"`,
   גרש בודד סוגר את המחרוזת ומפיל את **כל הסקריפט**. הגרשים מקודדים ל-`%27`.
3. **`#plat-bar`, `#cat-bar`, `#lang-sel`, `#theme-btn` נושאים סגנון inline.**
   גיליון סגנונות לא מנצח אותו — צריך `!important`.
4. **הבנייה כותבת ל-`docs/` ומסנכרנת דרך clone ב-`/tmp`.** בדיקה של
   `/root/repos/fashionhotspot-site/index.html` לפני `fashionhotspot-pull.sh`
   מציגה גרסה ישנה. זה כבר גרם לי לחשוב שתיקון לא עבד כשהוא כן עבד.
