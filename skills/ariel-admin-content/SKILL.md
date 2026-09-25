---
name: ariel-admin-content
description: עריכת קובצי התוכן של arielaizenshtat.com מהפאנל - עמודי האתר (site.md, about.md, facts.md, training.md, talks.md, faq.md, clients.md, download.md, העמודים המשפטיים), פרויקטים בתיק העבודות (work/<slug>.md: יצירה, עריכה, הסתרה, שחזור), והמשפטים הקבועים של ג׳רוויס (jarvis-lines.md). כולל בדיקת תקינות עם הפרסר של האתר לפני שמירה. הפעל על "תעדכן את הטקסט באתר", "תשנה את הביו", "פרויקט חדש", "תוסיף עבודה לתיק", "תסתיר את הפרויקט", "מה ג׳רוויס אומר כש", "תשנה את המשפט של ג׳רוויס", "שאלה נפוצה חדשה", "תעדכן את ההרצאות". Triggers - ariel content, site copy, work item, jarvis lines, תוכן האתר, תיק העבודות, פרויקט באתר, המשפטים של ג׳רוויס, עמוד אודות.
---

# תוכן האתר: עמודים, פרויקטים והמשפטים של ג׳רוויס

התוכן חי בקבצי markdown עם frontmatter בתיקיית `/content` של הריפו. הפאנל שומר **override** ב-Convex
(`contentFiles`); האתר קורא קודם את ה-override ואז את קובץ הריפו. "שחזור" מוחק את ה-override והריפו
חוזר. הכול דרך הסוד. חיבור והגדרות: `ariel-admin`. צורת כל קובץ: `references/content-shapes.md`.

```bash
ADMIN="python3 ~/.claude/skills/ariel-admin/scripts/ariel_admin.py"
$ADMIN query content:listContentFiles | jq '.[] | {path, deleted, updatedAt}'   # מה נערך בפאנל
$ADMIN content-get about.md -o /tmp/about.md          # override אם יש, אחרת קובץ הריפו המקומי
$ADMIN content-check about.md /tmp/about.md            # הפרסר של האתר, אותו אחד שהפאנל מסרב איתו
$ADMIN content-save about.md /tmp/about.md             # בודק ואז שומר; מסרב לקובץ שהאתר לא יקרא
```

`content-get` מדפיס `source`: `override` (נערך בפאנל), `repo` (רק בריפו; נקרא מ-`ARIEL_SITE_REPO`),
`deleted` (מוסתר) או `missing`. בלי ריפו מקומי אין דרך לקרוא קובץ שעוד לא נערך, ואז מבקשים מאריאל את
הטקסט או מעתיקים מהעורך בפאנל (`/admin/content/<path בלי .md>`).

## סדר העבודה לכל עריכה

1. `content-get` לקובץ מלא. עורכים את הקובץ המקומי, לא כותבים מאפס: ההערות `<!-- source: -->`
   ו-`<!-- TODO(ariel): -->` נשארות.
2. עריכה לפי הכללים למטה.
3. `content-check`. `ok: false` מחזיר `issues` עם שורה והסבר בעברית. מתקנים עד `ok: true`.
4. `python3 ~/human-voice-skill/human/scripts/check.py /tmp/<file>` על העברית.
5. `content-save`. הפלט מזכיר: העמודים מתעדכנים תוך 5 דקות, המוח של ג׳רוויס דקה אחריהם.
   רוצים מיד? לשמור מהפאנל.
6. `content-get --source override` לאימות, ואז לדווח לאריאל עם הקישור `/admin/content/<path>`.

## כללי התוכן

- **אין להמציא עובדות על אריאל.** מה שלא ידוע נכתב `<!-- TODO(ariel): מה חסר -->` בגוף, או
  `TODO(ariel)` כערך ב-frontmatter (הערך נופל, השדה לא מוצג). `TODO(ariel)` גלוי בגוף = הפרסר מסרב.
- **שמות לקוחות לא מופיעים.** Google, Meta, בזק, חברת החשמל, בשום קובץ. Gemini כמוצר מותר.
- **SYSTM במרכז, PixMind Studio אחריו.** מקור למידע על SYSTM: `/Users/a1234/systm/branding/BRANDBOOK.md`.
  בלי מחירים באתר.
- **עברית של בן אדם** (`~/.claude/NO-AI-VOICE.md`): בלי תקבולת שלילית, בלי מקף ארוך, בלי פסקת
  סיכום, בלי מילון ה-AI. הבודק `check.py` חייב לעבור.
- **ג׳רוויס מדבר על אריאל בגוף שלישי** ופונה למבקר בלשון ניטרלית ("אפשר לשאול אותי" במקום "אתה יכול").
- מונחים לועזיים בתוך עברית נשארים כמו שהם; האתר מטפל בכיוון (RTL).
- תיאור ה-SEO (`description` ב-`site.md`) עד 155 תווים; הפרסר בודק.
- שמות קבצים: אותיות לטיניות קטנות, ספרות ומקפים. נתיב חדש שלא ברשימה ב-`content-shapes.md` לא
  יוצג בשום מקום: העמודים קבועים בקוד, רק `work/<slug>.md` הוא פתוח להוספה.

## פרויקטים (תיק העבודות)

`work/<slug>.md` = פרויקט אחד, כתובת `/work/<slug>`, יעד לג׳רוויס `work:<slug>`. הפאנל עורך אותם
בטופס (`/admin/work`); מכאן כותבים את הקובץ עצמו. תבנית ב-`references/content-shapes.md`.

```bash
$ADMIN content-get work/dona-gracia.md -o /tmp/dona.md          # דוגמה קיימת לתבנית
$ADMIN content-save work/new-film.md /tmp/new-film.md            # פרויקט חדש = קובץ חדש
$ADMIN mutate content:deleteContentFile --args '{"path":"work/old.md"}' --yes    # הסתרה מהאתר
$ADMIN mutate content:restoreContentFile --args '{"path":"work/old.md"}' --yes   # ביטול ההסתרה / ביטול העריכה
```

- חובה: `title`, `client`, `summary`, `order`, `featured`, `draft`, ואחד מ-`video` (עם `poster`) או `image`.
- `draft: true` = מוסתר בפרודקשן. פרויקט חדש נשמר כ-`draft: true` עד שאריאל אישר.
- `video.provider`: `url` (mp4 מארח, כתובת https מלאה), `youtube`, `vimeo`, `mux`, `cloudflare` (מזהה בלבד).
  **וידאו לא נכנס לריפו ולא לאחסון של Convex כקובץ גדול**; ה-mp4 של אריאל יושבים אצלו (למשל
  heritage.pixmind.tv).
- פוסטר ותמונה: נתיב תחת `/public` (`/work/x.jpg`) או כתובת https, למשל URL מספריית המדיה
  (`ariel-admin-media`: `upload poster.jpg` מחזיר `url`, `width`, `height`).
- `category`: **slug** של קטגוריה מ-`categories:listCategories` (kind `work` או `both`).
- `keywords`: מילים שג׳רוויס מזהה בקול (איותים של שם הלקוח, שם המוצר).
- מחיקה אמיתית של קובץ ריפו לא קיימת מכאן; `deleteContentFile` מסתיר, והקובץ נשאר בגיט.

## המשפטים של ג׳רוויס (`jarvis-lines.md`)

פורמט: שורות `- <id>: <טקסט>` תחת כותרות. הפרסר בודק שכל המזהים הנדרשים (`REQUIRED_LINE_IDS` בקוד)
קיימים: **אין למחוק או לשנות שם של מזהה**, רק את הטקסט. שורה עם `{placeholder}` מתמלאת בזמן ריצה ולא
מוקלטת מראש; שורות בלי placeholder מוקלטות בקול של ג׳רוויס. אחרי שינוי טקסט של שורה כזאת, ההקלטה
בריפו כבר לא תואמת: להקליט מחדש עם `record-voice <id>` (סקיל `ariel-admin-ops`), אחרת המבקר ישמע את
הטקסט הישן.

הקול: רגוע, מדויק, יבש, קצר (זה נאמר בקול). אריאל בגוף שלישי, המבקר בלשון ניטרלית. קבוצות: `boot.*`,
`nav.arrive.*`, `intercept.link.*`, `clarify.*`, `control.*`, `error.*`, `contact.*`, `guides.*`,
`wake.*`, `holo.*`, `mouse.inert`, `cta.*`, `inapp.notice`, והצעות לכל עמוד בסוף הקובץ.

## מה כל קובץ עושה

| קובץ | עמוד | הערות |
|---|---|---|
| `site.md` | זהות, כותרת, תיאור SEO, רשתות, `legal` (פרטי העסק), `portraits` | `email` ו-`legal` הם TODO עד שאריאל ממלא |
| `facts.md` | המקום היחיד לעובדות על אריאל (למוח של ג׳רוויס) | כל עובדה פעם אחת, עם מקור |
| `about.md` | `/about`: כותרת, פתיח, ציר זמן, תמונה, גוף | |
| `training.md` | `/training`: תוכניות (`programs` עם `id`, `url`, `tempName`), מודולים | `tempName: true` מציג "שם זמני" |
| `talks.md` | `/talks`: נושאים, קהלים, איך מזמינים | |
| `faq.md` | שאלות נפוצות: `## שאלה` ואז תשובה | |
| `clients.md` | הערת הלקוחות ב-`/work` | הרשימה ריקה בהחלטת אריאל |
| `privacy.md`, `terms.md`, `cookies.md`, `refunds.md`, `accessibility.md`, `download.md` | עמודים פשוטים: `title`, `lead`, גוף, ו-`jarvis` (תקציר למוח) | שינוי משפטי: לעדכן גם `docs/LEGAL-REVIEW.md` בריפו |
| `jarvis-lines.md` | המשפטים הקבועים | ראה למעלה |
| `work/<slug>.md` | פרויקט | ראה למעלה |
