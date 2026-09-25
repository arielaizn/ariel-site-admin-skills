---
name: ariel-admin-analytics
description: קריאה וניתוח של האנליטיקס של arielaizenshtat.com מתוך הפאנל - צפיות, מבקרים, סשנים, מקורות, מכשירים, מדינות, פקודות לג׳רוויס (fast-path מול LLM), מה ג׳רוויס לא הבין, שיחות קול, HOLO ומחיאות כף, משפך המדריכים (צפייה, שער, הרשמה, הורדה), הודעות צור קשר, זמני תגובה (p50/p95), שגיאות, לידים לפי יום. הפעל על "כמה נכנסו לאתר", "מה קורה באנליטיקס", "כמה לידים השבוע", "מה אנשים שואלים את ג׳רוויס", "דוח שבועי", "איזה מדריך הכי חזק", "כמה זמן ג׳רוויס עונה", "מאיפה מגיעים". Triggers - ariel analytics, site analytics, jarvis analytics, אנליטיקס האתר, דוח מבקרים, סטטיסטיקות האתר.
---

# אנליטיקס של האתר

המקור: אירועי first-party שהאתר שולח ל-Convex (טבלת `events`), בלי פרטים אישיים (מזהים אקראיים, מחלקת מכשיר,
קוד מדינה, גיבוב IP יומי). PostHog הוא שכבה נפרדת ולא נגישה מכאן. שמירה: 180 יום.

```bash
ADMIN="python3 ~/.claude/skills/ariel-admin/scripts/ariel_admin.py"
$ADMIN overview                                  # 7 ימים + לידים, הודעות, מדריכים, מדיה, דיוור, שער
$ADMIN analytics --days 7 --brief                # המספרים הראשיים
$ADMIN analytics --days 30                       # ה-summary המלא
$ADMIN analytics --days 90 --section commands    # חלק אחד: commands, guides, latency, voice, jarvis, errors...
$ADMIN analytics --from 2026-09-01 --to 2026-09-15
$ADMIN query leads:leadStats                     # לידים לפי יום (30 יום) ומדריכים מובילים
$ADMIN query messages:messageStats
```

`--days N` הוא N ימים כולל היום (UTC). הסיכום מחושב בתוך Convex מעד 20,000 שורות; `capped: true` אומר
שכל מספר הוא רצפה, ואז מצמצמים את התקופה.

## מה יש בסיכום

השדות המלאים ב-`references/summary-fields.md`, שמות האירועים ב-`references/events.md`. הקבוצות:

| קבוצה | שדות |
|---|---|
| תנועה | `pageviews`, `visitors` (מזהה אקראי בדפדפן), `sessions`, `bounces` (סשן עם צפייה אחת), `dailyIps`, `pageviewsByDay`, `topPages`, `devices`, `countries`, `referrers`, `utmSources` |
| ג׳רוויס | `commands` (סך הכול, לפי כוונה, לפי מקור voice/text/suggestion, `fastpath` מול `llm`, ו-`unknown`: הטקסטים שלא הובנו עם ספירה ותאריך אחרון), `commandsByDay`, `jarvis` (הפעלות, boot, מיקרופון אושר או נדחה, קליקים שנתפסו, צ׳יפים, קישורים חיצוניים), `voice` (שיחות Gemini Live: התחלות, סיומים, משך חציוני ו-p95), `clap`, `holo` |
| מדריכים | `guides.views`, `gateShown`, `unlocked`, `downloads`, `byGuide` (משפך לכל מדריך), ו-`guides.leads` מטבלת `guideEvents` (מה שהשרת רשם למי שכבר נרשם) |
| צור קשר | `contact.submitted` (אירוע בדפדפן) לעומת `contact.messages` (שורות שנשמרו) |
| מהירות | `latency` לכל אבן דרך (`action_ready`, `cursor_start`, `speech_start`, `done`) בנפרד ל-fastpath ול-llm, עם `n`, `p50`, `p95` במילישניות |
| שגיאות | `errors` לפי קוד |
| מדיה | הפעלות וידאו, אודיו ותמונה, ו-`media.top` |

## איך עונים על שאלות נפוצות

**"כמה נכנסו השבוע?"** `analytics --days 7 --brief`: `pageviews`, `visitors`, `sessions`. להגיד את
שלושתם, כי הפער ביניהם הוא חלק מהתשובה (ממוצע עמודים לסשן, נטישה).

**"מה אנשים שואלים את ג׳רוויס ולא מקבלים תשובה?"** `analytics --days 30 --section commands` ואז
`commands.unknown`. זו הרשימה לשיפור ה-fast-path ותוכן ה-FAQ. ההצעה לאריאל: אילו טקסטים חוזרים, ולאיזה
עמוד או מדריך אפשר לחבר אותם. שינוי ה-fast-path עצמו הוא שינוי קוד בריפו, לא בפאנל.

**"איזה מדריך עובד?"** `guides.byGuide`: לכל slug, `views` → `gateShown` → `unlocked` → `downloads`.
אחוז ההרשמה = unlocked / gateShown. ליד עם `source` = slug מגיע מאותו מדריך (`query leads:leadStats`
נותן `topGuides` לפי צפיות והורדות של נרשמים).

**"ג׳רוויס איטי?"** `latency.done.llm.p95` לעומת `latency.done.fastpath.p95`. יעד הספק: fast-path מתחת
ל-300 מילישניות עד תזוזת הסמן, LLM מתחת ל-1.5 שניות עד תחילת הדיבור. `voice.medianMs` הוא משך שיחה, לא
זמן תגובה.

**"מאיפה מגיעים?"** `referrers` (דומיין מפנה), `utmSources`, `countries`. ישראל אמורה להוביל; מדינה זרה
בראש = בוטים או קמפיין.

## דוח לאריאל

עברית, 6 עד 10 שורות, מספרים בלבד בלי פרשנות מנופחת. מבנה מומלץ: תקופה, תנועה (3 מספרים), ג׳רוויס
(פקודות, אחוז fastpath, 3 טקסטים שלא הובנו), מדריכים (המשפך + המדריך החזק), לידים (`leadStats.last7d`,
`consented`), הודעות שלא נקראו, שגיאה בולטת אם יש. השוואה לתקופה הקודמת רק אם הרצת גם אותה (`--from/--to`).
לסיים במספר או בפעולה, בלי משפט מסכם. הטקסט עובר את `~/.claude/NO-AI-VOICE.md`.

## מה אין כאן

- מסלולי גלישה, הקלטות סשן, מפות חום: PostHog (כשמוגדר מפתח), מחוץ לחבילה הזאת.
- זהות של מבקר: אין. `visitorId` אקראי ואינו ליד. אין לחבר בין השניים.
- Vercel Analytics: אירועים דומים נשלחים גם לשם, לצפייה בדשבורד של Vercel בלבד.
