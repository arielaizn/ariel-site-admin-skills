# ariel-site-admin-skills

חבילת סקילים לניהול מלא של פאנל הניהול של arielaizenshtat.com מתוך סוכן (Claude Code, Codex, OpenClaw
וכל סוכן שקורא SKILL.md), בלי דפדפן: אנליטיקס, לידים והודעות, מדריכים וקטגוריות, תוכן העמודים
והפרויקטים, ספריית המדיה, דיוור, הגדרות, הקול של ג׳רוויס ויומן הפעולות.

מבנה האתר שהחבילה מניחה: Next.js 16 על Vercel, נתונים ב-Convex (פרודקשן `affable-kiwi-408`), פאנל
ב-`/admin` עם סיסמה אחת. נכון ל-25.09.2026.

## מה יש בפנים

| סקיל | תפקיד |
|---|---|
| `ariel-admin` | המרכזי: החיבור, הכלי `ariel_admin.py`, כללי בטיחות, ניתוב, וארבעה מסמכי עזר (כל פונקציות Convex, הסכמה, ה-API של הסשן, זמני הקאש) |
| `ariel-admin-analytics` | צפיות, מבקרים, פקודות לג׳רוויס, מה לא הובן, משפך המדריכים, זמני תגובה, שגיאות, דוח לאריאל |
| `ariel-admin-inbox` | לידים (חיפוש, ייצוא, הסכמה, מחיקה) והודעות מצור קשר |
| `ariel-admin-guides` | מדריכים חינמיים, קבצים, סקירה קולית, ערכות, קטגוריות |
| `ariel-admin-content` | קובצי התוכן: עמודים, פרויקטים (`work/<slug>.md`), המשפטים של ג׳רוויס, עם בדיקת הפרסר של האתר |
| `ariel-admin-media` | ספריית המדיה: העלאה, חיפוש, מחיקה עם בדיקת שימוש |
| `ariel-admin-mailing` | רשימות תפוצה, נמענים, טיוטות דיוור, הגדרות דיוור |
| `ariel-admin-ops` | שער ההרשמה, הקלטות הקול, יומן הפעולות, מצב האתר |

הכלי המשותף: `skills/ariel-admin/scripts/ariel_admin.py` (Python 3.9+, ספרייה סטנדרטית בלבד). הפלט JSON.

## התקנה

```bash
git clone git@github.com:arielaizn/ariel-site-admin-skills.git
cd ariel-site-admin-skills
./install.sh            # מעתיק את skills/* ל-~/.claude/skills ויוצר ~/.config/ariel-admin/.env
./install.sh --link     # קישורים סימבוליים במקום העתקה (עדכון עם git pull)
./install.sh --dest ~/.codex/skills     # יעד אחר
```

אחרי ההתקנה ממלאים את `~/.config/ariel-admin/.env` (תבנית ב-`.env.example`):

```bash
ARIEL_ADMIN_API_SECRET=      # ה-ADMIN_API_SECRET של דיפלוימנט ה-Convex. בריפו של האתר: npx convex env get ADMIN_API_SECRET --prod
ARIEL_ADMIN_PASSWORD=        # סיסמת הפאנל (ADMIN_PASSWORD ב-Vercel). נחוץ רק לייצוא CSV, ל-act ולהקלטת קול
```

ואז:

```bash
python3 ~/.claude/skills/ariel-admin/scripts/ariel_admin.py doctor
python3 ~/.claude/skills/ariel-admin/scripts/ariel_admin.py overview
```

## שתי דלתות

1. **Convex HTTP API** עם הסוד של השרת: כל פונקציית אדמין, קריאה וכתיבה. זו רוב העבודה.
2. **סשן אדמין** עם הסיסמה: ייצוא CSV, ה-API של ג׳רוויס בפאנל (`/api/admin/assistant/act`, שגם מרענן
   את הקאש של האתר), הקלטת שורת קול. עוגייה ל-12 שעות ב-`~/.cache/ariel-admin/`.

מה לא עובר דרך החבילה: שליחת דיוור ומייל בדיקה (רק מכפתור בפאנל, כי מפתח Resend יושב בשרת של Next),
דיפלוי ומשתני סביבה (Vercel), הקוד עצמו.

## בטיחות

- פעולות הורסות דורשות `--yes` (Convex) או `--confirmed` (act), ורק אחרי "כן" מפורש של אריאל.
- הכלי מסרב לפונקציות שהן צנרת פנימית של האתר (`analytics:ingest`, `campaigns:mark*`, `leads:upsertLead` ועוד).
- הסוד והסיסמה נקראים ממשתני סביבה בלבד, מושחרים מכל שגיאה, ולא נכנסים לריפו הזה (`.gitignore`).
- כל כתיבה נרשמת ביומן הפאנל כמו לחיצה.
- טקסט לאתר עובר את `~/.claude/NO-AI-VOICE.md` ואת `check.py` של `human-voice-skill`.

## עדכון החבילה כשהאתר משתנה

המקור לכל דבר כאן הוא הריפו של האתר: `convex/*.ts` (פונקציות וסכמה), `components/admin/assistant/kinds.ts`
ו-`lib/admin/assistant/server.ts` (ה-API של הסשן), `lib/content/*` (צורות התוכן). כשמוסיפים שם פונקציה,
שדה או kind, מעדכנים את `references/convex-functions.md`, את `references/session-api.md` ואת
`ariel_admin.py` (הרשימות `ALWAYS_YES`, `NEVER_CALL`, `conditional_yes`), ומריצים:

```bash
python3 skills/ariel-admin/scripts/ariel_admin.py --dev doctor
for f in $(find skills -name '*.md'); do python3 ~/human-voice-skill/human/scripts/check.py "$f" || echo "FAIL $f"; done
```

החבילה הקודמת (`ariel-site-*`, יולי 2026, Supabase) שייכת לאתר הישן ואינה תקפה. אם היא עדיין מותקנת
ב-`~/.claude/skills`, כדאי להסיר אותה כדי שהטריגרים לא יתנגשו.
