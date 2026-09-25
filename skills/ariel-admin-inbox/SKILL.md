---
name: ariel-admin-inbox
description: הלידים וההודעות של arielaizenshtat.com - מי נרשם למדריכים (שם, אימייל, הסכמה לדיוור, מקור, צפיות והורדות), חיפוש, דף ליד עם ההיסטוריה, ייצוא CSV, שינוי הסכמה, מחיקה לפי בקשת האדם, והודעות מטופס צור קשר (חדשות, נקראו, ארכיון, מחיקה, מענה). הפעל על "כמה לידים", "מי נרשם", "תוציא לי את הלידים", "יש הודעות חדשות", "מה כתבו לי", "תמחק את הליד", "הוא ביקש שימחקו אותו", "תסמן כנקרא". Triggers - ariel leads, ariel inbox, contact messages, לידים באתר, הודעות מהאתר, תיבת ההודעות, נרשמים למדריכים.
---

# לידים והודעות

לידים = מי שפתח את המדריכים החינמיים (שם + אימייל, פעם אחת לדפדפן, שנה). הודעות = טופס צור קשר (גם
בהכתבה לג׳רוויס). שניהם ב-Convex, קריאה וכתיבה דרך הסוד. חיבור והגדרות: `ariel-admin`.

```bash
ADMIN="python3 ~/.claude/skills/ariel-admin/scripts/ariel_admin.py"
```

## לידים

```bash
$ADMIN query leads:leadStats                                     # סך הכול, 7 ימים, מאשרי דיוור, לפי יום, מדריכים מובילים
$ADMIN query leads:listLeads --args '{"paginationOpts":{"numItems":50,"cursor":null}}'
$ADMIN query leads:listLeads --all                                # כולם (עד 20,000)
$ADMIN query leads:exportLeads | jq '.[] | select(.email|test("gmail"))'   # חיפוש חופשי ב-jq
$ADMIN query leads:getLead --args '{"leadId":"<id>"}'             # הליד + 200 האירועים האחרונים שלו
$ADMIN act query lead --args '{"email":"someone@example.com"}'    # דרך הסשן: חיפוש לפי אימייל
```

שדות: `name`, `email` (תמיד באותיות קטנות, אחד לכל כתובת), `marketingConsent`, `termsAcceptedAt` ו-
`consentVersion` (איזה נוסח סימן, מ-23.09.2026), `source` (slug של מדריך, `guides` לעמוד הרשימה, `jarvis`
להרשמה בקול), `createdAt`, `lastSeenAt`, `views`, `downloads`. אירועים: `unlock`, `view`, `download`
עם `slug` ו-`at`.

### ייצוא CSV (סשן)

```bash
$ADMIN export-leads -o leads.csv            # כולם
$ADMIN export-leads --consent -o consent.csv
$ADMIN export-leads --consent -o -          # ל-stdout
```

עמודות: `name,email,createdAt,source,views,downloads,marketingConsent`. UTF-8 עם BOM, אקסל פותח עברית
נכון. כל ייצוא נרשם ביומן (`lead.export`).

### הסכמה לדיוור

```bash
$ADMIN mutate leads:setMarketingConsent --args '{"leadId":"<id>","marketingConsent":false}' --yes
```

ההסכמה היא חוקית (חוק התקשורת סעיף 30א): ביטול מוריד את האדם מכל רשימות התפוצה, אישור מכניס אותו לרשימת
ברירת המחדל. **אישור הסכמה שהאדם לא נתן בעצמו אסור.** רק כשאריאל אומר שהאדם ביקש ממנו, ואז דרך
`lists:addMember` (סקיל `ariel-admin-mailing`), שמתעד את זה כ-`manual`.

### מחיקת ליד (בקשת מחיקה)

```bash
$ADMIN mutate leads:deleteLead --args '{"leadId":"<id>"}' --yes
```

מוחק את הליד, את כל האירועים שלו ואת השורות שלו ברשימות. העוגייה שלו מפסיקה לעבוד תוך דקה. לפני
`--yes`: להקריא לאריאל שם + אימייל ולקבל "כן". מחיקת בדיקות (שמות כמו "בדיקת שער", מקור `e2e-*`):
לזהות לפי `source` ולבקש אישור על הרשימה כולה פעם אחת.

## הודעות מצור קשר

```bash
$ADMIN query messages:messageStats
$ADMIN query messages:listMessages --args '{"paginationOpts":{"numItems":20,"cursor":null},"status":"new"}'
$ADMIN query messages:listMessages --all                          # הכול, כל הסטטוסים
$ADMIN mutate messages:setMessageStatus --args '{"id":"<id>","status":"read"}'      # read | archived | new
$ADMIN mutate messages:deleteMessage --args '{"id":"<id>"}' --yes
```

שדות: `name`, `email`, `topic` (`lecture` הרצאה, `training` הכשרה, `production` הפקה, `other`), `message`
(עד 2000 תווים), `createdAt`, `status`, `emailed` (העותק לאריאל יצא ב-Resend). אין פונקציית "הודעה אחת":
מסננים את הרשימה לפי `_id`.

**מענה.** מהחבילה הזאת לא שולחים מייל. כשאריאל רוצה לענות: לנסח טיוטה בעברית (בקול שלו, לפי
`~/.claude/ARIEL-VOICE.md`), להראות לו, והוא שולח מהמייל שלו. לינק מוכן: בפאנל, כפתור "מענה" פותח
`mailto:` עם הציטוט. אחרי מענה: `setMessageStatus` ל-`read`, ואם נסגר, `archived`.

## דיווח לאריאל

- לידים חדשים: שם, מקור (איזה מדריך), האם אישר דיוור. בלי להעתיק את כל האימיילים לצ׳אט אלא אם ביקש.
- הודעות: מי, נושא, שורה ראשונה, מתי. קישור: `/admin/messages?tab=new&open=<id>`.
- לידים בפאנל: `/admin/leads`, דף ליד: `/admin/leads/<id>`.

## פרטיות

הנתונים כאן הם מידע אישי לפי חוק הגנת הפרטיות. לא מעתיקים רשימות לידים לכלים חיצוניים, לא שומרים CSV
מחוץ למחשב של אריאל, ובקשת מחיקה של אדם מתבצעת בו ביום (`leads:deleteLead` + לוודא ב-`lists:listsOfEmail`
שלא נשאר). מי שלחץ על "הסרה" במייל כבר יצא מהרשימות וההסכמה שלו בוטלה; אין להחזיר אותו בייבוא.
