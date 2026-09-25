---
name: ariel-admin-ops
description: ההגדרות והתפעול של הפאנל ב-arielaizenshtat.com - שער ההרשמה למדריכים (פתיחה וסגירה), הגדרות הדיוור, מצב החיבורים של האתר (Gemini Live, המוח של ג׳רוויס, TTS, מייל, Convex), הקלטות הקול של ג׳רוויס (רשימה, הקלטה מחדש דרך Gemini Live בשרת, מחיקה), ויומן הפעולות של הפאנל (מי שינה מה ומתי). הפעל על "תכבה את שער ההרשמה", "תפתח את המדריכים לכולם", "מה השתנה בפאנל", "יומן הפעולות", "תקליט מחדש את המשפט", "ההקלטה של ג׳רוויס", "האם Gemini עובד", "מצב האתר". Triggers - ariel settings, guides gate, admin log, jarvis voice lines, שער ההרשמה, יומן הפאנל, הקול של ג׳רוויס, הגדרות האתר.
---

# הגדרות, קול ויומן

חיבור והגדרות של הכלי: `ariel-admin`.

```bash
ADMIN="python3 ~/.claude/skills/ariel-admin/scripts/ariel_admin.py"
$ADMIN overview
$ADMIN query settings:listSettings
$ADMIN act query settings              # סשן: השער + אילו חיבורים מוגדרים בשרת (live, brain, tts, sttServer, contactEmail, convex)
```

## שער ההרשמה למדריכים

`guidesGate` → `{enabled: true}` (ברירת המחדל, גם כשההגדרה חסרה). כבוי = כל מדריך פתוח לכולם, בלי
שם ואימייל, ואין לידים חדשים.

```bash
$ADMIN act act gate_on                       # מיידי (מרענן את הקאש בשרת)
$ADMIN act act gate_off --confirmed          # אחרי "כן" מפורש של אריאל
$ADMIN mutate settings:setSetting --args '{"key":"guidesGate","value":{"enabled":false}}' --yes   # דרך Convex: עד 30 שניות
```

לפני כיבוי לומר לאריאל: "המדריכים ייפתחו לכולם ולא יירשמו לידים חדשים. לבצע?".

## הגדרות אחרות

`mailing.senderAddress`, `mailing.autoEnroll`: סקיל `ariel-admin-mailing`. מפתחות אחרים לא קיימים היום;
`setSetting` על מפתח חדש ייצור אותו אבל האתר לא יקרא אותו. משתני סביבה (מפתחות API, מודל, קול) יושבים
ב-Vercel ולא בפאנל: `act query settings` רק מראה אם הם קיימים.

## הקול של ג׳רוויס

השורות הקבועות (`jarvis-lines.md`) מוקלטות מראש בקול של Gemini Live (Charon). הקלטה מהפאנל דורסת את
ההקלטה שבריפו לשורה אחת; מחיקה מחזירה את הריפו.

```bash
$ADMIN query voice:listVoiceLines                          # מה הוקלט מחדש: lineId, text, durationSec, url
$ADMIN record-voice control.stop                           # סשן; עד דקה; הטקסט נלקח מהתוכן הנוכחי
$ADMIN mutate voice:deleteVoiceLine --args '{"lineId":"control.stop"}' --yes
```

מתי מקליטים: אחרי ששינו טקסט של שורה ב-`jarvis-lines.md` (סקיל `ariel-admin-content`), אחרת המבקר
שומע את הטקסט הישן. שורה עם `{placeholder}` לא ניתנת להקלטה (422 `not_recordable`). `mismatch` = הקול
לא קרא בדיוק את הטקסט אחרי 3 ניסיונות: לנסח את השורה פשוט יותר ולנסות שוב. `quota` = מכסת Gemini,
לחכות. הקלטה אחת בכל פעם לשרת (409 `busy`). המבקרים שומעים את ההקלטה החדשה תוך דקה.

לפני הקלטה: להקריא לאריאל את הטקסט שיוקלט (`content-get jarvis-lines.md` + grep על המזהה).

## יומן הפעולות

```bash
$ADMIN query adminLog:listLog --args '{"limit":50}'                 # עד 200
$ADMIN query adminLog:listLog --args '{"limit":200}' | jq '.[] | select(.action|startswith("mailing."))'
$ADMIN act query log --args '{"n":20}'                               # עם תוויות בעברית
$ADMIN mutate adminLog:log --args '{"action":"agent.note","detail":"עודכן about.md לפי בקשת אריאל"}'
```

תחומים לפי תחילית: `guide`, `bundle`, `lead`, `message`, `content`, `voice`, `media`, `mailing`,
`category`, `setting`. הקודים המלאים והתוויות: `references/convex-functions.md` בסקיל המרכזי (סעיף
adminLog). "מה השתנה היום?" = לסנן לפי `at` מאז חצות (שעון ישראל) ולתרגם את הקודים לעברית.

## מצב האתר

```bash
$ADMIN doctor                                                        # הכלי, הסוד, האתר, הסשן, הריפו
curl -s -o /dev/null -w '%{http_code}\n' https://arielaizenshtat-site.vercel.app/
curl -s https://arielaizenshtat-site.vercel.app/api/voice/manifest | jq 'keys | length'
$ADMIN analytics --days 1 --section errors
```

תקלות שמופיעות כשגיאות באנליטיקס (`errors` לפי קוד) ובלוגים של Vercel; דיפלוי, משתני סביבה ומפתחות
הם עניין של הריפו ושל Vercel, מחוץ לחבילה הזאת. כשמשהו נראה שבור בפרודקשן: לדווח לאריאל מה נבדק
ומה התוצאה, בלי לשנות הגדרות "לניסיון".
