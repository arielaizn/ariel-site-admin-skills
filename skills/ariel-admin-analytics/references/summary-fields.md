# `analytics:summary` fields (convex/analytics.ts `AnalyticsSummary`)

`from`, `to`: the period in ms. `capped`: the period held more than 20,000 event rows and only the
first 20,000 (by time) were read; every number is then a lower bound. `eventCount`: rows read.

| field | type | meaning |
|---|---|---|
| `pageviews` | number | `pageview` events |
| `visitors` | number | distinct `visitorId` (random id in localStorage, one year) |
| `sessions` | number | distinct `sessionId` (random id per tab session) |
| `bounces` | number | sessions with exactly one pageview |
| `dailyIps` | number | distinct daily-salted IP hashes (a person counts once per day) |
| `pageviewsByDay` | `[{day, count}]` | every UTC day in the period, zero-filled, up to 400 days |
| `commandsByDay` | `[{day, count}]` | Jarvis commands per day |
| `topPages` | `[{key, count}]` | pathname → pageviews, top 20 |
| `topEvents` | `[{key, count}]` | event name → count, top 40 |
| `devices` | `[{key, count}]` | phone / tablet / desktop (pageviews) |
| `countries` | `[{key, count}]` | ISO country code from the request, top 20 |
| `referrers` | `[{key, count}]` | referring host (no path) when it was another site |
| `utmSources` | `[{key, count}]` | `utm_source` of the landing URL |
| `commands.total` | number | `command` events (a Jarvis turn that produced an action) |
| `commands.byIntent` | list | intent → count (navigate, answer, control, fill_lead, contact, ...) |
| `commands.bySource` | list | voice / text / suggestion |
| `commands.fastpath` / `commands.llm` | number | answered by the instant fast path vs. by the model |
| `commands.unknown` | `[{text, count, last}]` | `intent_unknown` texts, case-folded, top 50 by count |
| `voice.started` / `voice.ended` | number | Gemini Live sessions |
| `voice.totalMs` / `medianMs` / `p95Ms` | number | session durations from `voice_session_end` |
| `holo.on` / `off` / `calibrated` / `mouseBlocked` | number | camera control events; `mouse_blocked` = a real mouse click outside the console |
| `clap.wakes` / `clap.sleeps` | number | clap detections |
| `guides.views` | number | `guide_view` (a guide page opened) |
| `guides.gateShown` | number | the sign-up panel was shown |
| `guides.unlocked` | number | a sign-up completed (browser event) |
| `guides.downloads` | number | `guide_download` events plus server-recorded downloads |
| `guides.byGuide` | `[{slug, views, gateShown, unlocked, downloads}]` | the funnel per guide, top 20 |
| `guides.leads` | `{unlocks, views, downloads}` | rows of `guideEvents` (server side, unlocked visitors only) |
| `contact.submitted` | number | `contact_submitted` browser events |
| `contact.messages` | number | messages rows created in the period |
| `media` | `{video, audio, image, top}` | plays / opens and the top 10 items (`video:<id>`) |
| `latency` | per mark `{fastpath: {n,p50,p95}, llm: {...}}` | marks: `action_ready` (ms_action), `cursor_start` (ms_cursor), `speech_start` (ms_speech), `done` (ms_total); nearest-rank percentiles |
| `errors` | `[{key, count}]` | `error` events by `code`, top 20 |
| `jarvis.activated` | number | first activation per visit |
| `jarvis.bootDone` | number | boot sequence completed |
| `jarvis.micGranted` / `micDenied` | number | microphone permission |
| `jarvis.linkIntercepts` | number | clicks on internal links that Jarvis took over |
| `jarvis.suggestionClicks` | number | suggestion chips pressed |
| `jarvis.externalLinks` | number | outbound links opened (by Jarvis or intercepted) |

Derived numbers worth quoting: pages per session = pageviews / sessions; bounce rate = bounces /
sessions; fast-path share = fastpath / total; gate conversion = unlocked / gateShown; download rate =
downloads / unlocked.
