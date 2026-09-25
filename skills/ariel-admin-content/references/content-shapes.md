# Content file shapes (lib/content/types.ts, lib/content/index.ts in the site repo)

Every file: YAML frontmatter between `---` lines, then a markdown body. HTML comments anywhere are
stripped before rendering and before Jarvis reads the text; they hold `TODO(ariel)` notes and
`source:` notes. A frontmatter value that is exactly `TODO(ariel)` is dropped (the field is absent);
`TODO(ariel)` inside any other value or visible in the body is refused by the parser.

`checkContentFile(path, text)` is what the admin editor and the CLI's `content-check` run: the zod
schema of the file plus these rules. Issues come back with a `line`, an English `message` and a
Hebrew `he`.

## site.md (SiteContent)

```yaml
name: אריאל איזנשטט
nameEn: Ariel Aizenshtat
role: מייסד SYSTM, סוכני AI לעסקים. ...
tagline: סוכני AI לעסקים. רק זה.        # optional, under the role on the home page
description: "..."                       # SEO, 155 characters at most
social:
  - label: TikTok
    url: https://www.tiktok.com/@ariel.ai3316
email: TODO(ariel)                       # optional
legal:                                   # optional block; each field TODO(ariel) until filled
  businessName: TODO(ariel)
  registrationId: TODO(ariel)
  address: TODO(ariel)
  phone: TODO(ariel)
  email: TODO(ariel)
portraits:                               # optional: hero | training | talks | contact
  hero: { src: /photos/ariel-hero.webp, alt: "...", width: 1070, height: 1400 }
```

## about.md (AboutContent)

`title`, `lead`, `timeline: [{when, title, text}]`, `photo: {src, alt, width?, height?}` (optional), body.

## facts.md

Body only: the facts about Ariel, each once, as short markdown. This is the identity block of
Jarvis's knowledge base; the page leads repeat facts for visitors and are not sent to the model.

## training.md (TrainingContent)

`title`, `lead`, `programs: [{id, name, tempName, summary, points[], url?, linkLabel?}]`, optional
`modules: {<program id>: [..]}` (syllabus sections), body. `id` is ASCII (`onemanai`, `systm`,
`wordofleader`): it becomes the target `external:<id>` when `url` is set.

## talks.md (TalksContent)

`title`, `lead`, `topics: [{title, summary, audiences[]}]`, `booking` (how to book), body.

## faq.md

Body only: `## question` then the answer, repeated. Text before the first `##` is ignored.

## clients.md

`clients: [{name, logo?, logoApproved}]` (empty by Ariel's decision) and a body note shown on /work.

## privacy.md, terms.md, cookies.md, refunds.md, accessibility.md, download.md (SimplePage)

`title`, `lead`, optional `jarvis` (a short summary the model answers from instead of the whole legal
text), body.

## work/<slug>.md (WorkItem)

The slug: `^[a-z0-9][a-z0-9-]{0,99}$`. Template (what `/admin/work` writes):

```markdown
---
# Shape: WorkItem (lib/content/types.ts). Route /work/<slug>, target work:<slug>. Edited in /admin/work.
title: דונה גרציה
client: PixMind Heritage
year: "2025"                 # optional; quote it so YAML keeps a string
summary: דוקו-דרמה באורך 6:00 על דונה גרציה ...      # up to 600 chars, shown on the card
role: הפקה מלאה              # optional
category: heritage           # optional: a category SLUG (kind work or both)
tags:
  - דוקו-דרמה
  - היסטוריה
keywords:
  - Doña Gracia
  - האינקוויזיציה
order: 2                     # 0..9999, lower first
featured: true
video:                       # optional; needs poster
  provider: url              # url | youtube | vimeo | mux | cloudflare
  id: https://heritage.pixmind.tv/assets/video/gracia-720.mp4   # full https URL for url, the id otherwise
  poster: /work/dona-gracia.jpg      # /public path or https URL (media library)
  title: דונה גרציה
image:                       # optional; a project needs video or image
  src: /work/dona-gracia.jpg
  alt: תקריב של דונה גרציה ...
  width: 1600
  height: 666
draft: false                 # true = hidden in production
---

<!-- TODO(ariel): anything unknown goes here, never in the visible text. -->

The body: markdown paragraphs about the project. Ariel in third person, no client names that are off
the site, no prices.
```

Limits: title 160, client 120, year 20, summary 600, role 120, tag 60 (20 tags), keyword 80 (40),
alt 300, urls 2000, body 100,000. YAML scalars that look like numbers, booleans or dates get quotes.

## jarvis-lines.md

```markdown
---
# notes for editors (this block is ignored)
---

## פתיחה

- boot.greeting: שלום, אני ג׳רוויס, העוזר של אריאל איזנשטט. ...
- boot.return: חזרנו לאוויר. במה אפשר לעזור?
```

Every `- <id>: <text>` line is a line; everything else is ignored. Ids: lowercase, digits, `_`, dots.
The parser requires every id in `REQUIRED_LINE_IDS` (lib/jarvis/lines.ts):
`boot.greeting`, `boot.return`, `boot.deeplink.{about,work,guides,training,talks,contact}`,
`nav.arrive.{home,about,work,guides,guide_item,training,talks,contact,privacy,terms,cookies,refunds,accessibility,download,work_item}`,
`nav.already_here`, `nav.section`, `intercept.link.{1,2,3}`, `clarify.unknown`, `answer.unknown`,
`offtopic`, `filler.wait`, `degraded.notice`, `control.{back,mode_classic,mode_jarvis,back_none,mute,unmute,stop,scroll_down,scroll_up}`,
`video.{play,pause,none}`, `external.{opened,blocked}`, `error.{mic_denied,mic_unsupported,no_speech,network,rate_limited}`,
`contact.{start,ask_email,confirm_email,retry_email,ask_topic,ask_message,confirm_send,sending,sent,cancelled,not_sent,failed,missing}`,
`guides.{locked,ask_name,confirm_signup,unlocked}`, `wake.{greeting,sleep}`,
`holo.{ready,denied,calibrate,calibrated,calibrate_failed,mouse_locked}`, `mouse.inert`,
`cta.{guides,systm,contact,dismissed}`, `inapp.notice`.
The "הצעות" section at the end lists suggestion chips per page (up to 60 chars each, 3 shown).
