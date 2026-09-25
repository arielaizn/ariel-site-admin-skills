---
name: ariel-admin
description: הסקיל המרכזי לניהול ממשק הניהול של arielaizenshtat.com (האתר של ג׳רוויס) מתוך סוכן, בלי דפדפן. חיבור ל-Convex עם הסוד של השרת, התחברות לפאנל עם הסיסמה, פקודת overview, כללי בטיחות ומפת ניתוב לשאר סקילי ariel-admin-*. הפעל בכל בקשה על "האתר של אריאל", "ממשק הניהול", "הפאנל", "האדמין", "מה קורה באתר", "כמה לידים", "תעדכן באתר", "תפרסם באתר", או כשסקיל ariel-admin-* אחר צריך את פרטי החיבור. Triggers - ariel admin, manage ariel site, arielaizenshtat, jarvis site admin, אתר אריאל, פאנל הניהול, אדמין האתר.
---

# ניהול האתר של אריאל: הסקיל המרכזי

האתר: arielaizenshtat.com (עד חיבור הדומיין: https://arielaizenshtat-site.vercel.app). Next.js 16 על Vercel,
הנתונים ב-Convex, ג׳רוויס מנווט בו בקול. פאנל הניהול יושב ב-`/admin` והוא ממשק מעל אותן פונקציות Convex
שהסקילים כאן קוראים ישירות. אפשר לנהל הכול מהטרמינל: לידים, הודעות, מדריכים, תוכן, מדיה, דיוור, הגדרות,
הקול של ג׳רוויס, ואת כל האנליטיקס.

החבילה הקודמת (`ariel-site-*`, יולי 2026) עבדה מול Supabase באתר הישן. היא לא תקפה לאתר הזה.

## הכלי

```bash
ADMIN="python3 ~/.claude/skills/ariel-admin/scripts/ariel_admin.py"
$ADMIN doctor          # הבדיקה הראשונה בכל סשן: חיבור, סוד, אתר, סשן
$ADMIN overview        # כל המספרים בבת אחת
$ADMIN --help
```

הפלט תמיד JSON. שגיאה יוצאת ל-stderr עם קוד יציאה: 1 השרת סירב, 2 שימוש שגוי, 3 חסרה הגדרה.
הסוד והסיסמה לעולם לא מודפסים: כל טקסט שגיאה עובר השחרה.

## שתי דלתות

**1. Convex HTTP API** (`query`, `mutate`, `overview`, `analytics`, `upload`, `content-*`).
כל פונקציית אדמין ב-Convex מקבלת `secret` ובודקת אותו מול `ADMIN_API_SECRET` של הדיפלוימנט. הכלי מזריק
אותו לבד. זו הדרך לרוב העבודה: קריאה וכתיבה מלאה, בלי סשן.

```bash
$ADMIN query leads:leadStats
$ADMIN query leads:listLeads --all --args '{"paginationOpts":{"numItems":200,"cursor":null}}'
$ADMIN mutate messages:setMessageStatus --args '{"id":"<messageId>","status":"read"}'
```

**2. סשן אדמין** (`login`, `act`, `export-leads`, `export-list`, `record-voice`, `logout`).
התחברות עם הסיסמה של הפאנל, עוגייה חתומה ל-12 שעות בקובץ `~/.cache/ariel-admin/`. נחוץ רק למה שקורה בשרת
של Next ולא ב-Convex: ייצוא CSV, ה-API של ג׳רוויס בפאנל (שגם מרענן את הקאש של האתר), הקלטת שורת קול.

```bash
$ADMIN login
$ADMIN act query overview
$ADMIN act act guide_publish --args '{"slug":"claude-design-50-prompts"}'
$ADMIN export-leads --consent -o leads.csv
```

`login` נכשל עם `wrong_password`? לעצור. 5 ניסיונות ב-15 דקות נועלים את הכתובת.

## הגדרות (משתני סביבה)

הכלי קורא קודם `~/.config/ariel-admin/.env` (או `ARIEL_ENV_FILE`), ומשתנה שכבר קיים בסביבה גובר.

| משתנה | חובה | מה זה |
|---|---|---|
| `ARIEL_ADMIN_API_SECRET` | לדלת 1 | ה-`ADMIN_API_SECRET` של דיפלוימנט ה-Convex. בריפו של האתר: `npx convex env get ADMIN_API_SECRET --prod` |
| `ARIEL_ADMIN_PASSWORD` | לדלת 2 | סיסמת הפאנל (`ADMIN_PASSWORD` בהגדרות Vercel) |
| `ARIEL_CONVEX_URL` | לא | ברירת מחדל: פרודקשן `https://affable-kiwi-408.eu-west-1.convex.cloud` |
| `ARIEL_CONVEX_URL_DEV` | לא | ל-`--dev`: `https://moonlit-shepherd-589.eu-west-1.convex.cloud` |
| `ARIEL_SITE_URL` | לא | ברירת מחדל: `https://arielaizenshtat-site.vercel.app` |
| `ARIEL_SITE_REPO` | לא | הריפו המקומי של האתר (לקובצי תוכן שעוד אין להם override, ולבודק התוכן) |

חסר `ARIEL_ADMIN_API_SECRET`? לעצור ולבקש מאריאל. אין לנחש, אין לחפש בקבצים אחרים, ואין לכתוב אותו לשום קובץ
מלבד `~/.config/ariel-admin/.env`.

ברירת המחדל היא **פרודקשן**. `--dev` עובר לדיפלוימנט הפיתוח (הסוד שלו יכול להיות שונה).

## מי עושה מה

| המשימה | הסקיל |
|---|---|
| צפיות, מבקרים, פקודות לג׳רוויס, משפך המדריכים, זמני תגובה, שגיאות, מה ג׳רוויס לא הבין | `ariel-admin-analytics` |
| לידים (מי נרשם למדריכים), הודעות מטופס צור קשר, הסכמות, ייצוא, מחיקה | `ariel-admin-inbox` |
| מדריכים חינמיים, ערכות PDF, קטגוריות | `ariel-admin-guides` |
| קובצי התוכן: עמודי האתר, פרויקטים (`work/<slug>.md`), המשפטים של ג׳רוויס | `ariel-admin-content` |
| ספריית המדיה: העלאה, חיפוש, מחיקה | `ariel-admin-media` |
| רשימות תפוצה, נמענים, דיוורים (Resend) | `ariel-admin-mailing` |
| הגדרות (שער ההרשמה), הקלטות הקול של ג׳רוויס, יומן הפעולות | `ariel-admin-ops` |

## כללי בטיחות

1. **פעולה הורסת רק אחרי "כן" מפורש של אריאל.** מחיקה, הורדה מהאתר, ביטול הסכמה, שחזור קובץ, כיבוי השער.
   הכלי מסרב בלי `--yes` (ב-Convex) או `--confirmed` (ב-act). לפני שמבקשים אישור: לומר במשפט אחד מה יקרה
   ועל מי או על מה, עם שם ואימייל או עם slug.
2. **פונקציות שהכלי מסרב להריץ** (`NEVER_CALL` בסקריפט): `analytics:ingest`, `campaigns:mark*`,
   `campaigns:recordDeliveries`, `leads:upsertLead`, `leads:recordGuideEvent`, `lists:enrollLead`,
   `messages:createMessage`. הן שייכות לצנרת של האתר. שליחת דיוור עצמה קורית רק מכפתור בפאנל.
3. **כל כתיבה נרשמת ביומן** (`adminLog`) בדיוק כמו לחיצה בפאנל. אריאל רואה מה עשית.
4. **הקאש של האתר.** כתיבה דרך Convex מגיעה לעמודים תוך 5 דקות לכל היותר (תוכן ומדריכים), 30 שניות לשער.
   מיידי: דרך הפאנל, או דרך `act` (guide_publish, gate_on, gate_off). פירוט ב-`references/caching.md`.
5. **עברית של בן אדם.** כל טקסט שנכנס לאתר או נמסר לאריאל עובר `~/.claude/NO-AI-VOICE.md` והבודק
   `python3 ~/human-voice-skill/human/scripts/check.py <file>`.
6. **לא ממציאים עובדות על אריאל.** תוכן חסר נכתב כ-`<!-- TODO(ariel): ... -->`. שמות לקוחות
   (Google, Meta, בזק, חברת החשמל) לא מופיעים באתר. SYSTM במרכז, PixMind Studio אחריו.

## אחרי כל שינוי

1. לקרוא חזרה את הרשומה (`query`) ולוודא שהשינוי נשמר.
2. לבדוק באתר החי כשזה רלוונטי: `curl -s https://arielaizenshtat-site.vercel.app/<page> | grep "<טקסט>"`.
   לא מופיע? להמתין עד 5 דקות לפני שמסיקים שיש באג.
3. לדווח לאריאל בעברית, קצר, עם קישור לעמוד בפאנל: `/admin/leads/<id>`, `/admin/guides/<slug>`,
   `/admin/content/<path בלי .md>`, `/admin/campaigns/<id>`.

## עוד בחבילה

- `references/convex-functions.md`: כל פונקציה, הארגומנטים ומה חוזר.
- `references/schema.md`: הטבלאות והשדות.
- `references/session-api.md`: login, act (query kinds, act kinds), ייצוא, הקלטה.
- `references/caching.md`: מה מתרענן מתי.
