# Convex tables (convex/schema.ts in the site repo)

Every row also carries `_id` and `_creationTime`. Times are ms since the epoch.

| table | fields | indexes / notes |
|---|---|---|
| `guides` | slug, title, excerpt, category (NAME), level?, body (markdown), bodyHtml? (sanitized rich text), audioStorageId?, audioUrl?, audioTitle?, audioPublic?, coverStorageId?, coverWidth?, coverHeight?, pageImages[{storageId,width,height}], assets[{kind: pdf/video/audio/image, title, storageId, mime, bytes, width?, height?, durationSec?}], aliases?[], published, order, updatedAt, sourceHash? | by_slug, by_order |
| `bundles` | slug, title, category, storageId, bytes, pages, published, order, updatedAt, sourceHash? | one combined PDF per category |
| `leads` | name, email (lower-cased, unique), marketingConsent, termsAcceptedAt?, consentVersion?, source, createdAt, lastSeenAt, views, downloads | by_email, by_createdAt |
| `guideEvents` | leadId, slug, kind (unlock/view/download), at | by_lead, by_slug, by_at |
| `messages` | name, email, topic, message, createdAt, status (new/read/archived), emailed | by_createdAt, by_status |
| `contentFiles` | path, body, deleted?, updatedAt | by_path. An override of `/content/<path>`; `deleted: true` hides a repo file |
| `voiceLines` | lineId, text, storageId, mime, bytes, durationSec, voice, model, updatedAt | by_lineId |
| `settings` | key, value (any), updatedAt | by_key |
| `media` | storageId, name, kind (image/video/audio/pdf/other), mime, size, width?, height?, duration?, url, alt?, tags?[], createdAt (unique, increasing), updatedAt | by_createdAt, by_kind, by_storageId |
| `lists` | name, description?, key? (`updates` = the default list), createdAt, updatedAt | by_createdAt, by_key |
| `listMembers` | listId, leadId?, email, name, status (subscribed/pending_consent/unsubscribed), source (lead/manual), addedAt, unsubscribedAt? | by_list, by_email, by_list_email; one row per (list, email) |
| `campaigns` | listId, subject, preheader?, bodyMarkdown, advertisement, status (draft/sending/sent/failed), createdAt, updatedAt, sentAt?, total, sent, failed, testSentAt?, lastError? | by_createdAt, by_list |
| `deliveries` | campaignId, email, status (sent/failed), resendId?, error?, at | by_campaign; a `sent` row is never sent again |
| `categories` | name, slug (ASCII, unique), kind (guide/work/both), description?, order, createdAt, updatedAt | by_slug, by_kind |
| `adminLog` | action, detail, at | by_at |
| `events` | name, props (flat), path, ts, sessionId, visitorId, device, country?, referrer?, utm?, ipHash? | by_ts, by_name, by_session. Nothing personal; purged after 180 days |

Files live in Convex storage (`_storage`); rows hold storage ids and, for media rows, the public URL
computed once.
