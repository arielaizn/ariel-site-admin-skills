# Event names (lib/analytics-events.ts)

The ingest route accepts only these names. Props are flat primitives, strings clipped at 200 chars,
24 props per event.

| event | when | useful props |
|---|---|---|
| `pageview` | every route change | (path, device, country, referrer, utm on the row) |
| `boot_done` | the boot sequence finished | |
| `jarvis_activated` | first voice/text activation of the visit | |
| `mic_permission_granted` / `mic_permission_denied` | microphone prompt | |
| `command` | a turn produced an action | `intent`, `target`, `source` (voice/text/suggestion), `fastpath` (bool), `ms_action`, `ms_cursor`, `ms_speech`, `ms_total` |
| `intent_unknown` | the turn had no answer | `text` |
| `contact_submitted` | the contact form went out | |
| `link_click_intercepted` | a click on a link that Jarvis took over | `external` (bool) |
| `external_link` | an outbound link opened | `id` |
| `suggestion_click` | a suggestion chip | `text` |
| `voice_session_start` / `voice_session_end` | Gemini Live conversation | `ms` on end |
| `clap_wake` / `clap_sleep` | clap detection | |
| `holo_on` / `holo_off` / `holo_calibrated` | camera control | |
| `mouse_blocked` | a trusted mouse click outside the console on desktop | |
| `mode_classic` / `mode_jarvis` | the visitor switched modes | |
| `cta_shown` / `cta_answer` | the quiet-time nudge and its chip | `id`, `answer` |
| `install_prompt` / `install_done` | PWA install | |
| `guide_view` / `guide_gate_shown` / `guide_unlocked` / `guide_download` | the guides funnel | `slug` |
| `video_play` / `audio_play` / `image_open` | media on a page | `id` |
| `error` | a client-side failure | `code` |

Not every event is aggregated by `analytics:summary` (`cta_*`, `install_*`, `mode_*` appear only in
`topEvents`).
