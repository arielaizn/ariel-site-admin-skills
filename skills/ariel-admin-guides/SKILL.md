---
name: ariel-admin-guides
description: ניהול המדריכים החינמיים של arielaizenshtat.com (עמוד /guides מאחורי הרשמה חד-פעמית) - רשימה, מדריך מלא, יצירת מדריך חדש בטקסט (markdown), עריכה, פרסום והורדה מהאתר, סדר, מחיקה, כריכה, עמודי PDF, קובץ PDF, סקירה קולית, ערכות (bundles) וקטגוריות של מדריכים ופרויקטים. הפעל על "תפרסם את המדריך", "תוריד את המדריך", "מדריך חדש", "תסדר את המדריכים", "תחליף כריכה", "איזה מדריכים יש", "קטגוריה חדשה", "תעביר את המדריך לקטגוריה". Triggers - ariel guides, free guides, guide publish, מדריכים באתר, המדריכים החינמיים, קטגוריות המדריכים, ערכת PDF.
---

# מדריכים, ערכות וקטגוריות

הציבור רואה כרטיסים (כותרת, תקציר, כריכה, עמוד ראשון). הטקסט המלא, שאר העמודים וה-PDF נפתחים אחרי
שם + אימייל (השער, הגדרה `guidesGate`). כל הכתיבה כאן דרך `adminGuides:*` ו-`categories:*` עם הסוד.
חיבור והגדרות: `ariel-admin`. הפונקציות המלאות: `~/.claude/skills/ariel-admin/references/convex-functions.md`.

```bash
ADMIN="python3 ~/.claude/skills/ariel-admin/scripts/ariel_admin.py"
$ADMIN query adminGuides:listAllGuides
$ADMIN query adminGuides:getGuide --args '{"slug":"claude-design-50-prompts"}'
$ADMIN query adminGuides:listAllBundles
$ADMIN query categories:listCategories
```

## פרסום, הורדה, סדר

```bash
$ADMIN act act guide_publish --args '{"slug":"<slug>"}'              # מרענן את האתר מיד (סשן)
$ADMIN act act guide_unpublish --args '{"slug":"<slug>"}' --confirmed
$ADMIN act act guide_reorder --args '{"slug":"<slug>","direction":"first"}'   # up | down | first | last
$ADMIN mutate adminGuides:setGuidePublished --args '{"slug":"<slug>","published":true}'   # דרך Convex: עד 5 דקות
$ADMIN mutate adminGuides:reorderGuides --args '{"slugs":["a","b","c"]}'
$ADMIN mutate adminGuides:setBundlePublished --args '{"slug":"<bundle>","published":false}' --yes
```

`act` מוצא מדריך גם לפי כותרת (`{"title":"50 פרומפטים"}`); כשיש כמה התאמות הוא מחזיר `candidates`,
ואז שואלים את אריאל. מדריך בלי עמודים ובלי טקסט אי אפשר לפרסם.

## מדריך חדש בטקסט (בלי PDF)

```bash
$ADMIN mutate adminGuides:createGuide --args '{
  "slug":"agents-checklist","title":"צ׳קליסט לסוכן ראשון","excerpt":"עשר בדיקות לפני שסוכן AI נוגע בלקוח אמיתי.",
  "category":"סוכני AI","level":"מתחילים","body":"# צ׳קליסט\n\n1. ...","aliases":["צ׳קליסט סוכנים"],"published":false
}'
$ADMIN mutate categories:ensureCategory --args '{"name":"סוכני AI","use":"guide"}'   # שהקטגוריה תהיה ברשימה
```

כללים: `slug` באנגלית קטנה, ספרות ומקפים, 2 עד 80 תווים, ייחודי. `category` הוא **שם** הקטגוריה (בדיוק
כמו ב-`categories:listCategories`). `body` הוא markdown; `bodyHtml` שייך לעורך העשיר בפאנל ולא נשלח
מכאן. הטקסט עצמו עובר `~/.claude/NO-AI-VOICE.md` והבודק `check.py` לפני השמירה, וכל עובדה בו מגיעה
מאריאל. יוצרים כ-`published: false`, מראים לאריאל, ואז מפרסמים.

עדכון: `adminGuides:updateGuide` עם כל השדות, גם אלה שלא השתנו (קודם `getGuide`, משנים, שולחים את הכול).

## קבצים: כריכה, עמודים, PDF, אודיו

העלאה לאחסון בלי שורה בספריית המדיה (הקובץ שייך למדריך):

```bash
$ADMIN upload cover.webp --no-register        # → {storageId, width, height, url}
$ADMIN mutate adminGuides:setGuideFiles --args '{"slug":"<slug>","cover":{"storageId":"<id>","width":800,"height":880}}' --yes
```

`setGuideFiles` מחליף רק מה שנשלח (`cover`, `pageImages`, `assets`, `audio`); מה שלא נשלח נשאר. קובץ
שהוחלף נמחק מהאחסון אלא אם הוא בספריית המדיה. לכן `--yes`.

**מדריך מ-PDF.** בפאנל (`/admin/guides/new`) הדפדפן מרנדר עמודים עם pdf.js. מהטרמינל אותו דבר ידני:

```bash
pdftoppm -r 110 -png guide.pdf page             # או ImageMagick; webp עדיף לגודל
for f in page-*.png; do $ADMIN upload "$f" --no-register --compact; done   # לשמור storageId+width+height לכל עמוד
$ADMIN upload guide.pdf --no-register --compact  # ה-PDF עצמו
$ADMIN mutate adminGuides:setGuideFiles --args '{"slug":"<slug>",
  "pageImages":[{"storageId":"...","width":1240,"height":1754}, ...],
  "assets":[{"kind":"pdf","title":"PDF","storageId":"...","mime":"application/pdf","bytes":123456}]}' --yes
```

עד 60 עמודים, PDF עד 40MB. הכריכה בדרך כלל היא העמוד הראשון.

**סקירה קולית** (קובץ אודיו מהספרייה, `ariel-admin-media`):

```bash
$ADMIN upload review.mp3 --name "סקירה: <כותרת>"     # שורה בספרייה, מחזיר url
$ADMIN mutate adminGuides:setGuideAudio --args '{"slug":"<slug>","audio":{"storageId":"<id>","url":"<url>","title":"סקירה קולית"},"audioPublic":false}'
$ADMIN mutate adminGuides:setGuideAudio --args '{"slug":"<slug>","audio":null}'      # הסרה
```

`audioPublic: true` משמיע אותה גם למי שלא נרשם.

## מחיקה

```bash
$ADMIN mutate adminGuides:deleteGuide --args '{"slug":"<slug>"}' --yes
```

מוחק את המדריך, הקבצים שלו (חוץ מקובצי ספריית המדיה) ואת אירועי ה-`guideEvents` שלו. לפני `--yes`:
הכותרת המלאה ומספר הלידים שהגיעו ממנו (`leads:leadStats` → `topGuides`). לרוב עדיף להוריד מהאתר
(`published: false`) ולא למחוק.

## קטגוריות

```bash
$ADMIN query categories:categoryUsage                                   # כמה מדריכים ופרויקטים בכל אחת
$ADMIN mutate categories:createCategory --args '{"name":"וידאו AI","kind":"both","description":"..."}'
$ADMIN mutate categories:updateCategory --args '{"id":"<id>","name":"וידאו ב-AI","kind":"both"}' --yes   # שינוי שם מעדכן את המדריכים
$ADMIN mutate categories:reorderCategories --args '{"ids":["<id1>","<id2>"]}'
$ADMIN mutate categories:deleteCategory --args '{"id":"<id>"}' --yes    # מסורב כל עוד מדריך או פרויקט משתמש בה
```

`kind`: `guide`, `work` או `both`. מדריכים נושאים את השם, פרויקטים (`work/<slug>.md`, שדה `category`)
את ה-slug; ה-slug נגזר מהשם (עברית מתועתקת: "בדיקה" → `bdykh`) ואפשר לשנות אותו רק כשאין פרויקט עליו.
`categoryUsage` לא רואה פרויקטים שקיימים רק בריפו; לפני מחיקה לבדוק גם `content-get work/<slug>.md`
לכל פרויקט.

## ערכות (bundles)

PDF אחד שמאגד את כל מדריכי הקטגוריה. מכאן רק פרסום/הורדה (`setBundlePublished`). ערכה חדשה נוצרת
בריפו של האתר עם `npm run guides:seed`.

## אחרי שינוי

`query adminGuides:listAllGuides` לאימות; באתר: `https://arielaizenshtat-site.vercel.app/guides` (עד 5
דקות דרך Convex, מיד דרך `act`). דיווח לאריאל עם `/admin/guides/<slug>`.
