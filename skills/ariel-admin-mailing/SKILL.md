---
name: ariel-admin-mailing
description: דיוור מהפאנל של arielaizenshtat.com דרך Resend - רשימות תפוצה (רשימת ברירת המחדל "עדכונים, מדריכים וניוזלטר" וכל רשימה אחרת), נמענים (הוספה מהלידים שאישרו, הוספה ידנית של מי שביקש, הסרה, סטטוס ממתין להסכמה), טיוטות דיוור ב-markdown, מצב שליחה ומשלוחים, הגדרות כתובת השולח והצטרפות אוטומטית, וייצוא CSV. הפעל על "תכין ניוזלטר", "טיוטת מייל לרשימה", "מי ברשימת התפוצה", "תוסיף אותו לרשימה", "כמה נרשמו לניוזלטר", "מה קרה עם הדיוור", "רשימה חדשה". Triggers - ariel mailing, newsletter, campaign draft, mailing list, רשימת תפוצה, ניוזלטר, דיוור, קמפיין מייל.
---

# דיוור: רשימות, נמענים, דיוורים

הכללים החוקיים כתובים בקוד של Convex (חוק התקשורת סעיף 30א): נמען מקבל מייל רק כשהוא `subscribed`,
וזה קורה רק עם הסכמה מפורשת. חיבור והגדרות: `ariel-admin`. הפונקציות: `references/convex-functions.md`
שם.

```bash
ADMIN="python3 ~/.claude/skills/ariel-admin/scripts/ariel_admin.py"
$ADMIN query lists:memberStats
$ADMIN query lists:listLists                      # ברירת המחדל ראשונה, עם ספירות
$ADMIN query campaigns:listCampaigns
```

## איך אנשים נכנסים לרשימה

1. הרשמה למדריכים מכניסה כל נרשם לרשימת ברירת המחדל (`key: updates`). עם הסימון של הדיוור הוא
   `subscribed`, בלי הסימון `pending_consent` (רואים אותו, לא שולחים לו). ההגדרה `mailing.autoEnroll`
   (`consenting` ברירת מחדל, או `all`) קובעת אם גם בלי סימון הוא מקבל מייל; `all` הוא החלטה של אריאל
   ודורש `--yes`.
2. הוספה מהלידים לרשימה אחרת עובדת רק על לידים עם `marketingConsent`. Convex בודק שוב ומדלג על השאר.
3. הוספה ידנית פירושה שמישהו ביקש מאריאל ישירות. `lists:addMember` מסמן `source: manual` ומעדכן את
   ההסכמה בליד. אין להוסיף ידנית בלי שאריאל אמר שהאדם ביקש.
4. הסרה בקישור במייל מוציאה מכל הרשימות ומבטלת את ההסכמה בליד. ייבוא הבא לא יחזיר אותו.

```bash
$ADMIN query lists:listMembers --all --args '{"listId":"<listId>"}'
$ADMIN query lists:listMembers --args '{"listId":"<listId>","paginationOpts":{"numItems":50,"cursor":null},"status":"pending_consent"}'
$ADMIN query lists:pickerLeads --args '{"listId":"<listId>"}'            # לידים עם הסכמה + הסטטוס שלהם ברשימה
$ADMIN mutate lists:addMembersFromLeads --args '{"listId":"<listId>","all":true}'
$ADMIN mutate lists:addMembersFromLeads --args '{"listId":"<listId>","leadIds":["<id>","<id>"]}'
$ADMIN mutate lists:addMember --args '{"listId":"<listId>","name":"דנה","email":"dana@example.com"}'
$ADMIN mutate lists:removeMember --args '{"memberId":"<memberId>"}' --yes
$ADMIN query lists:listsOfEmail --args '{"email":"dana@example.com"}'
$ADMIN export-list <listId> -o list.csv                                   # סשן
```

`addMembersFromLeads` מחזיר דוח: `added`, `resubscribed`, `skippedNoConsent`, `skippedOnList`,
`skippedMissing`. לדווח את המספרים כמו שהם.

## רשימות

```bash
$ADMIN mutate lists:createList --args '{"name":"בוגרי ההכשרה","description":"..."}'
$ADMIN mutate lists:updateList --args '{"listId":"<id>","name":"...","description":"..."}'
$ADMIN mutate lists:deleteList --args '{"listId":"<id>"}' --yes        # לא לברירת המחדל; מוחק גם נמענים, דיוורים ומשלוחים
$ADMIN mutate lists:ensureDefaultList                                   # יוצר את ברירת המחדל אם נמחקה
```

## דיוורים

טיוטה = נושא, פרה-הדר, גוף ב-markdown פשוט (פסקאות, כותרות, מודגש, קישורים, רשימות), ורשימת יעד.
`advertisement: true` מוסיף "פרסומת" לתחילת הנושא (חובה כשהמייל מוכר משהו; `false` רק לעדכון שאינו
פרסומת). לכל מייל מתווספים לבד: שם השולח, כתובת השולח מההגדרה, קישור הסרה חתום, וכותרות
List-Unsubscribe.

```bash
$ADMIN mutate campaigns:createCampaign --args '{
  "listId":"<listId>","subject":"מדריך חדש: צ׳קליסט לסוכן ראשון","preheader":"עשר בדיקות לפני הלקוח הראשון",
  "bodyMarkdown":"שלום {שם},\n\n...","advertisement":true
}'
$ADMIN query campaigns:getCampaign --args '{"campaignId":"<id>"}'       # כולל כמה subscribed ברשימה
$ADMIN mutate campaigns:updateCampaign --args '{"campaignId":"<id>","listId":"<listId>","subject":"...","bodyMarkdown":"...","advertisement":true}'
$ADMIN mutate campaigns:deleteCampaign --args '{"campaignId":"<id>"}' --yes      # טיוטה או דיוור שנעצר בלבד
$ADMIN query campaigns:deliveriesFor --args '{"campaignId":"<id>","paginationOpts":{"numItems":100,"cursor":null},"status":"failed"}'
```

אין placeholders אישיים בגוף (המערכת לא מחליפה `{שם}`); כותבים פנייה כללית. הטקסט בקול של אריאל
(`~/.claude/ARIEL-VOICE.md`), עובר `~/.claude/NO-AI-VOICE.md` ו-`check.py`, ומוצג לאריאל לפני שנשמר.

**שליחה ומייל בדיקה קורים רק מהפאנל**: `/admin/campaigns/<id>`, הכפתורים "שליחת בדיקה אליי" (ל-
`ADMIN_EMAIL`) ו"שליחה" (קבוצות של 100 ב-Resend, כל קבוצה נרשמת לפני הבאה; דיוור שנעצר ממשיכים באותו
כפתור ומי שקיבל לא מקבל שוב). מהטרמינל מכינים את הטיוטה ומדווחים לאריאל שהיא מוכנה עם הקישור.
הפונקציות `campaigns:mark*` ו-`recordDeliveries` שייכות ללולאת השליחה והכלי מסרב להן.

סטטוסים: `draft`, `sending` (יותר מ-10 דקות בלי עדכון = תקוע, מותר להתחיל שוב מהפאנל), `sent`, `failed`
(`lastError` אומר למה; דומיין לא מאומת ב-Resend הוא הסיבה הנפוצה).

## הגדרות

```bash
$ADMIN query settings:getSetting --args '{"key":"mailing.senderAddress"}'
$ADMIN mutate settings:setSetting --args '{"key":"mailing.senderAddress","value":"רחוב ..., עיר"}'   # מודפס בתחתית כל מייל (חובה חוקית)
$ADMIN mutate settings:setSetting --args '{"key":"mailing.autoEnroll","value":"consenting"}'
```

כתובת שולח ריקה = המיילים יוצאים בלי כתובת פיזית; לפני דיוור ראשון לוודא שהיא מלאה.

## דיווח לאריאל

רשימה: שם, `subscribed` / `pending` / `unsubscribed`, כמה דיוורים יצאו. דיוור: נושא, רשימה, סטטוס,
`sent`/`failed` מתוך `total`, `lastError` אם יש. קישורים: `/admin/lists/<id>`, `/admin/campaigns/<id>`.
