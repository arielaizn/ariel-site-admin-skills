# What refreshes when

The admin pages themselves read Convex fresh on every request. The public site caches.

| what you changed | the site shows it | Jarvis knows it | instant path |
|---|---|---|---|
| a content file (`content:saveContentFile`) | ≤ 5 min (`CONTENT_REVALIDATE = 300`) | ≤ 1 min after that (brain memo 60 s) | save from `/admin/content` or `/admin/work` (updateTag + revalidatePath) |
| a guide's text, order, publish state | ≤ 5 min (`GUIDES_REVALIDATE = 300`); the full guide behind the gate ≤ 1 min (`FULL_TTL_MS`) | with the guides list | `act act guide_publish` / `guide_unpublish` / `guide_reorder`, or the admin editor |
| the guides gate (`guidesGate`) | ≤ 30 s (`GATE_TTL_MS`) per server instance | | `act act gate_on` / `gate_off` |
| a category | with the guides / work pages (≤ 5 min) | | the admin categories page |
| a voice line (record or delete) | ≤ 60 s (the CDN holds `/api/voice/manifest` for 60 s) | | |
| media row edits | immediately where the URL is used | | |
| leads, messages, lists, campaigns, settings, log | admin only (dynamic) | | |
| analytics events | the next `analytics:summary` call | | |

`content:restoreContentFile` and `content:deleteContentFile` follow the same 5-minute rule; through
`act act content_restore` the refresh is immediate (that act drops the override, so use it only when
that is what Ariel wants).

Vercel's edge also keeps prerendered HTML of public pages until the layout is revalidated; a save in
the admin does that. A Convex-only write waits for the time limits above.
