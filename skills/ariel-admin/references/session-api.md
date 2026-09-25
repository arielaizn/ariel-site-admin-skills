# The admin session: what the Next server does that Convex does not

`ariel_admin.py` handles all of this (`login`, `act`, `export-leads`, `export-list`, `record-voice`,
`logout`). This page is the contract behind those commands.

## Login

`POST /api/admin/login`, JSON `{"password": "..."}`, `Content-Type: application/json`, no `Origin`
header (the route refuses cross-site browser requests; a plain HTTP client is fine).

| status | body | meaning |
|---|---|---|
| 200 | `{ok: true, next}` + `Set-Cookie: jarvis_admin=v1.<expiresAtMs>.<nonce>.<hmac>` | signed in for 12 hours |
| 401 | `{error: "wrong_password"}` | stop; do not loop |
| 429 | `{error: "rate_limited", retryAfterSec}` | 5 attempts per 15 minutes per IP |
| 503 | `{error: "not_configured"}` | the site has no password / session secret |

The cookie is httpOnly, Secure, SameSite=Strict. The CLI keeps it in `~/.cache/ariel-admin/` (mode 600)
and logs in again by itself when it has expired and `ARIEL_ADMIN_PASSWORD` is set.

`POST /api/admin/logout` ends it.

## Jarvis's admin API: `POST /api/admin/assistant/act`

The same tools Jarvis uses inside the panel (Ctrl+J). Body:

```json
{"name": "query", "kind": "<query kind>", "args": {...}}
{"name": "act",   "kind": "<act kind>",   "args": {...}, "confirmed": true|false}
```

Answers `{ok: true, ...}` or `{ok: false, error}`. 409 = a destructive act without `confirmed`.
Rate limit on the token route only; this route has none beyond the session.

**Query kinds** (read only): `overview`, `leads` (n, q, consentOnly), `lead` (id or email), `messages`
(status, n), `message` (id), `guides`, `guide` (slug or title), `media` (mediaKind, q, n), `settings`
(gate + which integrations are configured: live, brain, tts, sttServer, contactEmail, convex), `analytics`
(days: 7, 30 or 90), `log` (n), `unknown_intents` (days), `content_files`.

**Act kinds**: `guide_publish`, `guide_unpublish`*, `guide_reorder` (slug, direction up/down/first/last),
`message_read`, `message_archive`, `message_delete`* (id), `lead_consent_withdraw`*, `lead_delete`* (id or
email), `gate_on`, `gate_off`*, `content_restore`* (path), `voice_delete`* (lineId), `media_delete`* (id),
`export_leads` (consentOnly; returns the download URL).
`*` = needs `confirmed: true`.

Why use `act` when Convex can do the same: these acts also refresh the site's caches at once
(guides tag, content tag, gate cache), find a guide by its title, and write the same log rows.
`args.n` is capped at 50 rows; for full lists use the Convex door.

## CSV exports

- `GET /api/admin/leads/export[?consent=1]`: every lead (or consenting leads only). UTF-8 BOM, CRLF,
  columns `name,email,createdAt,source,views,downloads,marketingConsent`. Writes `lead.export` to the log.
- `GET /api/admin/lists/<listId>/export`: one list's members, columns
  `name,email,status,source,addedAt,unsubscribedAt`.

## Re-record a Jarvis line

`POST /api/admin/voice/record`, `{"lineId": "control.stop"}`. The server records the line through
Gemini Live (same voice as the site), checks the take against the text, stores it in Convex and answers
`{ok, line: {lineId, text, url, mime, bytes, durationSec, updatedAt}, takes, score}`. The text always
comes from the current `jarvis-lines.md` (repo or override), never from the request.

| status | meaning |
|---|---|
| 404 `unknown_line` | no such id in jarvis-lines.md |
| 422 `not_recordable` | the line has `{placeholders}` |
| 422 `mismatch` | the takes did not match the text closely enough (`spoken`, `score`) |
| 409 `busy` | one recording at a time per server |
| 429 `quota` | Gemini quota |
| 503 `no_key` / `no_convex` | the server is missing a key |

One call takes up to a minute.
