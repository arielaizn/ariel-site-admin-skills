---
name: ariel-admin-media
description: ספריית המדיה של הפאנל ב-arielaizenshtat.com - העלאת תמונות, וידאו, אודיו ו-PDF לאחסון של Convex עם רישום בספרייה, חיפוש, סטטיסטיקות, שינוי שם, alt ותגיות, מחיקה עם בדיקת שימוש (מדריך, ערכה, שורת קול או קובץ תוכן שמשתמשים בקובץ חוסמים מחיקה), וקבלת URL ציבורי לשימוש כפוסטר או כתמונה בפרויקט. הפעל על "תעלה את התמונה", "תוסיף לספריית המדיה", "איזה קבצים יש", "תמחק את הקובץ", "אני צריך URL לתמונה", "כמה מקום המדיה תופסת". Triggers - ariel media, media library, upload to site, ספריית המדיה, העלאת קובץ לאתר, פוסטר לפרויקט.
---

# ספריית המדיה

כל קובץ שאריאל העלה בפאנל: שורה ב-`media` עם URL ציבורי קבוע, והקובץ עצמו באחסון של Convex. מדריכים,
פרויקטים (לפי URL) ובוחר הקבצים בפאנל קוראים מכאן. חיבור והגדרות: `ariel-admin`.

```bash
ADMIN="python3 ~/.claude/skills/ariel-admin/scripts/ariel_admin.py"
$ADMIN query media:mediaStats
$ADMIN query media:listMedia --args '{"limit":40}'
$ADMIN query media:listMedia --args '{"kind":"image","q":"פוסטר"}'      # kind: image | video | audio | pdf | other
$ADMIN query media:getMedia --args '{"id":"<id>"}'
$ADMIN act query media --args '{"mediaKind":"pdf","n":20}'                 # דרך הסשן
```

דפדוף: `nextCursor` הוא ה-`createdAt` של השורה האחרונה; מעבירים אותו כ-`cursor` בקריאה הבאה.

## העלאה

```bash
$ADMIN upload ./poster.jpg --alt "פוסטר של הסרט דונה גרציה"
$ADMIN upload ./review.mp3 --name "סקירה קולית: 50 פרומפטים"
$ADMIN upload ./kit.pdf
$ADMIN upload ./page-01.webp --no-register       # אחסון בלבד, בלי שורה בספרייה (עמודי מדריך)
```

הפלט: `storageId`, `url`, `mime`, `bytes`, ולתמונות `width` ו-`height` (הכלי קורא PNG, JPEG, GIF, WebP).
עם רישום, גם `media` (השורה המלאה). שלושה צעדים מאחורי הקלעים: `files:generateUploadUrl`, `POST` של
הבייטים עם `Content-Type` נקי (בלי `; codecs=`, Convex דוחה), ואז `media:createMedia`.

- שם קובץ: מה שנותנים ב-`--name`, אחרת שם הקובץ. עד 200 תווים. `alt` עד 300, תגיות עד 20.
- וידאו כבד לא עולה לכאן. mp4 של סרטים יושבים בשרת של אריאל (heritage.pixmind.tv) ובפרויקט מציינים
  `provider: url` עם הכתובת. לספרייה נכנסים קליפים קצרים בלבד.
- אסטים חדשים באים מאריאל או נוצרים בסקיל `gpt-image-2`; לא מקשרים לתמונות מאתרים אחרים.

## שימוש ב-URL

- פוסטר או תמונה בפרויקט: `video.poster` / `image.src` בקובץ `work/<slug>.md` (סקיל
  `ariel-admin-content`) מקבלים את ה-`url` כמו שהוא, עם `width`/`height` מהפלט.
- כריכת מדריך: העלאה עם `--no-register` ואז `adminGuides:setGuideFiles` (סקיל `ariel-admin-guides`).
  קובץ מהספרייה שמשמש כריכה נשאר בספרייה גם כשמחליפים אותו במדריך.
- סקירה קולית: העלאה רגילה (עם רישום) ואז `adminGuides:setGuideAudio` עם `storageId` + `url`.

## עריכה ומחיקה

```bash
$ADMIN mutate media:updateMedia --args '{"id":"<id>","name":"שם חדש","alt":"...","tags":["פוסטר","2026"]}'
$ADMIN mutate media:deleteMedia --args '{"id":"<id>"}' --yes
```

מחיקה מחזירה `{ok:false, usedBy:[...]}` כשמשהו עדיין משתמש בקובץ (תוויות בעברית: "מדריך: ...",
"ערכה: ...", "שורת קול: ...", "תוכן: work/x.md"), ואז שום דבר לא נמחק. קודם מסירים את השימוש,
אחר כך מוחקים. לפני `--yes`: שם הקובץ בקול רם לאריאל.

`files:deleteFile --yes` מוחק קובץ אחסון יתום (בלי שורה); רק כשידוע שאין עליו הפניה.

## דיווח

שם, סוג, גודל ב-MB (הפלט בבייטים), וה-URL כשמישהו צריך אותו. הפאנל: `/admin/media`.
