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

## מה נשאר

| נושא | סטטוס |
|------|--------|
| **209 כרטיסי אמזון בלי תמונה** | חסום עד PA-API, שמגיע **עם אישור** תוכנית השותפים. עד אז מוצג אריח קטגוריה. ה-hook ב-`build-static.js` כבר מחכה למפתחות `AMAZON_PAAPI_*` |
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
