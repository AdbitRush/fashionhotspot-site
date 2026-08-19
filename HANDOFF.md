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

## 2026-08-19 — שני עיצובים, עם מתג

**באתר יש עכשיו שני עיצובים.** כפתור בהדר (`List view` / `Card view`) מחליף
ביניהם, הבחירה נשמרת ב-localStorage כ-`fh-design`.
**ברירת המחדל היא העיצוב הישן** — מבקר רגיל לא רואה שינוי עד שהבעלים יחליט.

### איך זה בנוי — לקרוא לפני שינוי כרטיס

זה **skin שני על אותו markup**, לא תבנית שנייה. כל הכללים תחת
`html[data-design="list"]` (79 כללים). מקור אחד לכרטיסים מזין את שני העיצובים,
כך שאי אפשר שאחד ידרוף מהשני.

| מלכודת | פירוט |
|---|---|
| **כרטיסים נבנים פעמיים** | `cardHTMLServer` ל-24 הראשונים, `cardHTML` בדפדפן לשאר. תיקנתי את האמוג'י רק בראשון — והוא נשאר על כל השורות הנראות, כי הנראות הן מהשני. **שינוי בכרטיס = שינוי בשניהם.** |
| **הקובץ הוא template literal אחד** | backtick בתוך **הערה** סוגר את המחרוזת באמצע הדף. הפיל build. |
| **הצ'יפים מקבלים צבע inline מ-JS** | `b.style.background` בכל render, צבע לכל קטגוריה. inline מנצח כל selector → `!important` הוא הכרחי, לא עצלות. מתועד כבר ל-`#plat-bar`/`#cat-bar`. |
| **הקרוסלה כותבת transform/filter/opacity inline בכל frame** | אותו דבר — כל override צריך `!important`. |

### מקור העיצוב

נבדקו **DealNews** ו-**Slickdeals** בפועל. כל בחירה למטה היא משהו ששניהם עושים
והאתר הזה עשה הפוך: ירוק לחיסכון (אדום = אזעקה), שורות במקום רשת (260px → 135px
לשורה), תמונה קטנה ליד טקסט, בלי גרדיאנטים, בלי pulse/glare/zoom.
ההנחה **הורדה בכוונה** — בפיד שבו כמעט הכל 52-57% הנחה, תג אדום פועם הוא רעש.

### ההדר — היה שבור, לא רק מכוער

`--hdr-fill` / `--hdr-line` / `--hdr-ink` **היו בשימוש ומעולם לא הוגדרו** בקובץ.
כל אחד מהם היה invalid at computed-value time: המילויים נפלו ל-transparent
והטקסט שרד רק בזכות ירושה מצבע ההדר. עכשיו מוגדרים.

הבעלים דיווח "the top still gray difficult to read" — וזה היה באג שלי:
`#design-btn` לקח `--ink` מהעמוד בזמן שהוא יושב על הדר כהה = **1.63:1**.
אותו כשל בדיוק שתועד 12 שעות קודם. ההדר עכשיו **בהיר** בתמה הבהירה, מה שמבטל
את הצורך במקרה מיוחד: ברגע שההדר חולק את משטח העמוד, `--ink` ו-`--save` פשוט
נכונים עליו. תמה כהה שומרת הדר כהה.

| | לפני | אחרי |
|---|---|---|
| ניווט / לוגו | — | 15.67:1 |
| placeholder בחיפוש | `#C9C2D2` = **1.5:1** על לבן | 6.79:1 |
| כפתורים בהדר | **1.63:1** | 15.67:1 |
| מחיר בקרוסלה | `--amber` = **1.61:1** | 15.67:1 |
| כותרת בקרוסלה | `#B7A9CC` = **2.20:1** | 8.74:1 |

שתי השורות האחרונות תוקנו **בשני העיצובים** — סריקת הניגודיות הקודמת תיקנה שלושה
משטחים ופספסה את הקרוסלה.

> ❓ **פתוח להחלטת הבעלים:** האם `list` הופך לברירת המחדל. עד שיחליט, המבקרים
> רואים את העיצוב הישן.

---

## 2026-08-19 — צבעים, מחירים, ותרגומים חלקיים

**הכל מחכה בריפו `whatsapp-deals-bot`, לא פורסם.** ה-job הלילי ב-01:00 UTC
יפרסם אותו לבד, או `node build-static.js` ידנית.

| מה | פירוט |
|---|---|
| **טקסט שחור על רקע שחור** | האתר עוצב dark-first והתמה הבהירה הולבשה עליו כ-token overrides. שלושה משטחים מוגבהים שמרו רקע כהה **קשיח** בזמן שהטקסט שלהם הגיע מ-token: `#toast` (`background:#171028` עם `color:var(--ink)`), `#find-modal`, `.car-item`. ניגודיות נמדדה: **1.17:1**. עכשיו `--elev`/`--on-elev`, 15.2-15.7:1 בבהיר ו-16.6:1 בכהה. `d3df0dd` |
| | ⚠️ כל משטח מוגבה חדש חייב לקחת את **שני** החצאים מאותו זוג. לקיחת אחד בלי השני היא בדיוק מה שגרם לזה. |
| | חמישה משטחים נוספים השתמשו ב-`rgba(255,255,255,.03-.06)` — שכבה לבנה מעל רקע קרם, כלומר בלתי נראית. עברו ל-`--glass` שמודע לתמה. |
| **הנחות מפוברקות** | מדידה על 15,068 שורות חיות: **14,451 (96%) הציגו הנחה**, מרוכזות ב-52-57%, ו-546 עם מחיר מקורי של **בדיוק פי 2.00**. זהו עוגן מחיר של עליאקספרס, לא מחיר שמישהו גבה. `creditableOrigPrice()` מסנן את הפי-2 ואת מה שמעל 70%. ירד ל-63%. `57e8a71` |
| | ❓ **נותר להחלטת הבעלים:** גם אשכול ה-52-57% ששרד הוא ארטיפקט של הפיד. הסרתו לגמרי היא החלטה עסקית, לא תיקון באג. |
| **למה המחיר באתר שונה מהעמוד** | ה-API מתמחר **SKU אחד**, לא מוצר. אותו מוצר, אותה שנייה: `country=US` → $30.91, `IL` → $18.62, בלי הפרמטר → $24.60. שש קריאות זהות עם `country=IL` נתנו מחיר זהה ו-sku זהה — כלומר **לא** התיישנות ולא אקראיות, ולכן הרצה חוזרת של הרענון מעולם לא עזרה. `skuId` נשמר עכשיו בכל שורה כדי לאפשר את התיקון האמיתי: `link.generate` על `/item/<id>.html?sku_id=<sku>`. |
| **תרגומים — הושלם** | 107 מפתחות בשש השפות, **0 מחרוזות אנגלית דולפות** ב-he/es/fr/de/el (נבדק בדפדפן). `db6fdbb` |
| **bidi — היה שבור, חמור מהצפוי** | ל-`.num`/`.iso` **לא היה כלל CSS בכלל**, כך שהעטיפה בספאנים לא עשתה כלום. וחשוב מכך: אלמנט שמכיל **רק מספר**, בלי עברית לידו, מתהפך גם הוא כשהדף `dir="rtl"` — הטיקר צייר `70%-` במקום `-70%`, וה-hero צייר `+1,468` במקום `1,468+`. 12 כללי `unicode-bidi:isolate` נוספו. |
| **כותרות מוצר בעברית באתר האנגלי** | 27% מהכרטיסים (394 מ-1,468). בארכיון רק 3% כאלה — כלומר בעיית **בחירה**: `dedupeDeals` שומר שורה אחת למוצר והעברית ניצחה. `fix-titles.js` שחזר 781 כותרות מה-API ושומר את העברית כ-`titleHe` (לאתר יש גרסה עברית). **ירד ל-10% (166).** השאריות הן שורות בלי `productId` — לשחזר מזהה ולהריץ שוב. `ca04dde` |

---

## סטטוס נוכחי

*(עודכן 2026-08-14 — הטבלה הקודמת כאן תיארה מצב מלפני שבוע)*

| | |
|--|--|
| דילים בעמוד הראשי | **1321** — אמזון 482 · AliExpress 736 · ישראל 103 |
| צ'יפים | All / AliExpress / Amazon / Israel — צ'יפ שמסנן ל-0 מסתתר לבד |
| מדריכים | 35 מאמרים × 6 שפות (en/he/es/fr/de/el) = 210 עמודים |
| מדריכים — affiliate | **אמזון + AliExpress** (10 + 10 קישורים לעמוד) |
| תמונות | **1321 מתוך 1321 עם תצלום אמיתי — 0 אריחי קטגוריה** |
| מחירים | כל 1321 עם מחיר; 456 מכרטיסי אמזון גם עם דירוג |
| קטגוריות | 16, ולכולן יש דילים של אמזון |
| מובייל 375px / 428px | אין גלילה אופקית, אזורי מגע 44px |
| ניגודיות | light mode נסרק — 401 צמתי טקסט, 0 כשלים ב-WCAG AA |

### שני מפתחות שונים ב-`site-config.json` — לא לבלבל
```jsonc
{
  "affiliates": { "amazon": true, "aliexpress": true,  "israel": true },
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

Two rules govern what may appear, and both are worth understanding before
changing anything:

1. **Product Advertising Content — price, list price, star rating, review count
   and the product image — may only be displayed if it came from PA-API.**
   PA-API exists only after approval. So none of it can be shown *legitimately*
   before then, no matter where it was obtained.
2. **Amazon's Conditions of Use forbid scraping.** Search pages already refuse
   plain HTTP (2.3KB stub, zero results) and product pages started returning
   CAPTCHAs after ~450 automated fetches from one IP in an afternoon.

**The site currently publishes that content anyway.** That is a deliberate
owner decision taken on 2026-08-14, with the risk stated: the homepage should
show Amazon working — real products, real photographs, real prices — so a
reviewer can see the site is capable of the job. The reasoning is that a
refusal can be answered by switching it off and reapplying.

| Surface | What it shows today | Notes |
|---|---|---|
| Homepage grid | **1,321 deals** — Amazon 482, AliExpress 736, Israel 103. Every row has a photo AND a price. Zero placeholders. | Amazon rows carry scraped images, prices and ratings. `feed.amazon: true` + `amazon_pa_content: true`. |
| Amazon coverage | all 16 categories, none empty | 183 products were harvested in a browser session specifically to fill garden, health, office, tools and travel, which had none. |
| 35 buying guides | ~2,200 words each × 6 languages, **10 Amazon search links + 10 AliExpress links** per guide | Search links need no PA-API — this half is compliant either way. AliExpress was switched back on 2026-08-14; it had been off since 08-09 for a review that was never submitted, earning nothing from either network. |
| Disclosure | "We are not an Amazon Associate and earn nothing from Amazon links today." | True before, during and after an application — needs no edit on the day you submit. |

### The one switch that controls it

```jsonc
// site-config.json
"amazon_pa_content": true   // publish Amazon images + prices (no PA-API)
"amazon_pa_content": false  // withhold until PA-API keys exist
```

`build-static.js` resolves both gates through a single predicate:

```js
showAmazonPA() = hasPaapi() || SITE_CONFIG.amazon_pa_content === true
```

so this is a one-line config change, not a code edit. It flipped three times on
2026-08-14 as hand edits to two functions before being made a config value —
don't put it back in the code.

**Nothing is ever deleted when it is switched off.** `archive.json` keeps all
~482 Amazon products with verified images (`resolve-amazon-images.js` checked
every URL returns ≥300px) and prices. The gates withhold at build time only, so
flipping the switch either way is instant and lossless.

---

## After acceptance — the order to do things in

The acceptance email is not the finish line; Amazon closes accounts that make no
qualifying sales. Do these in order.

### 1. On the day the email arrives (10 minutes)

```jsonc
// fashionhotspot-site/site-config.json
"amazon_associate_status": "approved",
"amazon_pa_content": false     // <- turn it OFF, not on
```

This is the counter-intuitive one, so it is first. Scraped Product Advertising
Content on a **live** Associates account is a different order of risk from the
same content on a site that has merely applied: before approval the worst case
is a refusal you can answer and resubmit; after approval it is account closure,
which is far harder to undo and takes the commission with it.

Cards will look thin for the gap between acceptance and PA-API access. That gap
is the price of the account surviving, and it closes at step 2.

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
