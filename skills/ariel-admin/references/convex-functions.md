# Convex functions of arielaizenshtat.com (admin surface)

Every function below is called as `module:function`. The CLI adds `secret` to the arguments; the
lists here show the other arguments only. Convex ids are opaque strings (`js777aakhd...`); a
`v.id('leads')` argument takes the string as it came back from a query. `paginationOpts` is
`{"numItems": N, "cursor": null}` on the first call and `{"numItems": N, "cursor": "<continueCursor>"}`
afterwards; the result is `{page, isDone, continueCursor}`. The CLI's `query --all` follows the
cursors for you.

Times are milliseconds since the epoch. Days in stats are UTC `YYYY-MM-DD`.

Public queries (no secret) exist too: `guides:listPublished`, `guides:getBySlug`, `guides:listBundles`,
`categories:listPublicCategories`, `voice:voiceManifest`. They return teaser fields only.

## analytics

| function | kind | args | returns |
|---|---|---|---|
| `analytics:summary` | query | `from`, `to` (ms) | the whole `AnalyticsSummary` (see ariel-admin-analytics/references/summary-fields.md). Reads at most 20,000 event rows; `capped: true` means every number is a lower bound. |
| `analytics:ingest` | mutation | never from the CLI | the site's event pipeline |

Retention: a nightly cron deletes events older than 180 days.

## leads

| function | kind | args | returns / notes |
|---|---|---|---|
| `leads:listLeads` | query | `paginationOpts`, `search?` | newest first; `search` filters the returned page by name or email (substring) |
| `leads:exportLeads` | query | | every lead, newest first, up to 20,000 rows |
| `leads:getLead` | query | `leadId` | `{lead, events}`: the row plus its last 200 guide events (`unlock`, `view`, `download`) |
| `leads:leadExists` | query | `leadId` (string) | boolean |
| `leads:leadStats` | query | | `{total, last7d, consented, byDay[30], topGuides[10]}` |
| `leads:setMarketingConsent` | mutation, `--yes` | `leadId`, `marketingConsent` | also moves the person on or off the mailing lists (`lists.syncLeadConsent`) and logs `lead.consent` |
| `leads:deleteLead` | mutation, `--yes` | `leadId` | deletes the lead, its events and its list memberships; logs `lead.delete` |
| `leads:upsertLead` | mutation | never from the CLI | the sign-up gate |
| `leads:recordGuideEvent` | mutation | never from the CLI | the site records views and downloads |

Lead row: `name`, `email` (lower-cased), `marketingConsent`, `termsAcceptedAt?`, `consentVersion?`,
`source` (a guide slug, `guides` or `jarvis`), `createdAt`, `lastSeenAt`, `views`, `downloads`.

## messages (contact form)

| function | kind | args | notes |
|---|---|---|---|
| `messages:listMessages` | query | `paginationOpts`, `status?` (`new`, `read`, `archived`) | newest first |
| `messages:messageStats` | query | | `{unread, read, archived, total}` |
| `messages:setMessageStatus` | mutation | `id`, `status` | |
| `messages:deleteMessage` | mutation, `--yes` | `id` | logs `message.delete` |
| `messages:createMessage` | mutation | never from the CLI | the contact form |

Message row: `name`, `email`, `topic` (`lecture`, `training`, `production`, `other`), `message` (up to
2000 chars), `createdAt`, `status`, `emailed` (Resend accepted the copy to Ariel).

## adminGuides (guides and bundles, full data)

| function | kind | args | notes |
|---|---|---|---|
| `adminGuides:listAllGuides` | query | | every guide in display order: slug, title, excerpt, category, published, order, updatedAt, pages, hasPdf, hasBody, hasAudio, coverUrl |
| `adminGuides:getGuide` | query | `slug` | one guide in full: body, bodyHtml, aliases, level, cover, audio, pageImages (with URLs), assets (with URLs) |
| `adminGuides:getFullBySlug` | query | `slug` | same, published guides only (what an unlocked visitor gets) |
| `adminGuides:listAllBundles` | query | | slug, title, category, bytes, pages, published, order, url |
| `adminGuides:getBundleFile` | query | `slug` | a published bundle's file |
| `adminGuides:createGuide` | mutation | `slug`, `title`, `excerpt`, `category`, `level?`, `body`, `bodyHtml?`, `aliases?`, `published` | slug: `^[a-z0-9][a-z0-9-]{1,79}$`, unique. Files come afterwards. Returns the id. |
| `adminGuides:updateGuide` | mutation | `slug` + the same fields | an absent `bodyHtml` turns the guide back into a markdown guide |
| `adminGuides:setGuidePublished` | mutation (`--yes` for false) | `slug`, `published` | logs `guide.publish` / `guide.unpublish` |
| `adminGuides:reorderGuides` | mutation | `slugs[]` | listed first = lowest order |
| `adminGuides:setGuideFiles` | mutation, `--yes` | `slug`, `cover?` `{storageId,width,height}`, `pageImages?` `[{storageId,width,height}]`, `assets?` `[{kind,title,storageId,mime,bytes,width?,height?,durationSec?}]`, `audio?` | arguments left out keep their value; files no longer referenced are deleted unless the media library owns them |
| `adminGuides:setGuideAudio` | mutation | `slug`, `audio?` (`null` removes; `{storageId, url?, title?}` attaches), `title?`, `audioPublic?` | the voice review |
| `adminGuides:deleteGuide` | mutation, `--yes` | `slug` | files and events go too |
| `adminGuides:setBundlePublished` | mutation (`--yes` for false) | `slug`, `published` | |

Limits: title 160, excerpt 600, category 60, level 40, alias 120 (20 aliases), body 400,000 chars,
bodyHtml 600,000. New bundles come only from the repo's `scripts/seed-guides.ts`.

## categories

| function | kind | args | notes |
|---|---|---|---|
| `categories:listCategories` | query | `kind?` (`guide` or `work`) | every category in display order: `_id, name, slug, kind, description, order` |
| `categories:categoryUsage` | query | | guides and admin-saved projects per category (repo-only projects are not counted here) |
| `categories:createCategory` | mutation | `name`, `kind` (`guide`, `work`, `both`), `description?` | the slug is derived (Hebrew is transliterated) and unique |
| `categories:updateCategory` | mutation, `--yes` | `id`, `name`, `kind`, `description?`, `slug?`, `projectsInUse?` | a rename moves every guide carrying the old name; narrowing the kind is refused while the other type uses it |
| `categories:deleteCategory` | mutation, `--yes` | `id`, `projectsInUse?` | refused while a guide or a project uses it |
| `categories:reorderCategories` | mutation | `ids[]` | |
| `categories:ensureCategory` | mutation | `name`, `use` (`guide` or `work`) | returns the category, creating or widening it |
| `categories:seedFromGuides` | mutation | | one-time import of the names the guides carry; safe to repeat |

Guides carry the category NAME; projects (`work/<slug>.md`) carry the SLUG.

## content (overrides of /content)

| function | kind | args | notes |
|---|---|---|---|
| `content:listContentFiles` | query | | every override: `path, body, deleted, updatedAt` |
| `content:getContentFile` | query | `path` | one override or null (null = only the repo file exists) |
| `content:saveContentFile` | mutation | `path`, `body` | path `^(?:[a-z0-9-]+\.md\|work/[a-z0-9-]+\.md)$`, body up to 200,000 chars; logs `content.save`. No validation here: use the CLI's `content-save`, which runs the site's parser first. |
| `content:deleteContentFile` | mutation, `--yes` | `path` | hides the file from the site (the repo file stays in git) |
| `content:restoreContentFile` | mutation, `--yes` | `path` | drops the override |

## media (the library)

| function | kind | args | notes |
|---|---|---|---|
| `media:listMedia` | query | `kind?`, `q?`, `limit?` (≤100), `cursor?` (createdAt of the last row) | `{items, nextCursor}`; `q` scans the newest 500 rows by name, alt, tags and mime |
| `media:getMedia` | query | `id` | |
| `media:mediaStats` | query | | count and bytes, total and per kind |
| `media:createMedia` | mutation | `storageId`, `name`, `kind`, `mime`, `size`, `width?`, `height?`, `duration?`, `alt?` | registers an uploaded file; returns the row with its public `url`; logs `media.upload` |
| `media:updateMedia` | mutation | `id`, `name?`, `alt?`, `tags?` | |
| `media:deleteMedia` | mutation, `--yes` | `id` | `{ok:false, usedBy:[...]}` when a guide, bundle, voice line or content file still uses it; nothing is deleted then |

## files (storage)

| function | kind | args | notes |
|---|---|---|---|
| `files:generateUploadUrl` | mutation | | a one-time URL; `POST` the bytes to it with a bare `Content-Type`, the answer is `{storageId}` |
| `files:getFileUrl` | query | `storageId` | public URL |
| `files:deleteFile` | mutation, `--yes` | `storageId` | a file no row points at |

## lists and members (mailing)

| function | kind | args | notes |
|---|---|---|---|
| `lists:listLists` | query | | default list first; each with `subscribed, pending, unsubscribed, campaigns, isDefault` |
| `lists:getList` | query | `listId` | |
| `lists:memberStats` | query | | totals across lists |
| `lists:listMembers` | query | `listId`, `paginationOpts`, `status?`, `search?` | |
| `lists:exportMembers` | query | `listId` | every member row (≤20,000) |
| `lists:subscribers` | query | `listId` | who a campaign goes to: subscribed, one per address |
| `lists:pickerLeads` | query | `listId` | leads with consent, with their status on this list |
| `lists:listsOfEmail` | query | `email` | the lists an address is on |
| `lists:ensureDefaultList` | mutation | | creates "עדכונים, מדריכים וניוזלטר" when missing; returns its id |
| `lists:createList` | mutation | `name`, `description?` | |
| `lists:updateList` | mutation | `listId`, `name`, `description?` | |
| `lists:deleteList` | mutation, `--yes` | `listId` | refused for the default list and while a campaign is sending; members, campaigns and deliveries go too |
| `lists:addMembersFromLeads` | mutation | `listId`, `leadIds?[]` or `all: true` | only leads with `marketingConsent`; returns `{added, resubscribed, skippedNoConsent, skippedOnList, skippedMissing}` |
| `lists:addMember` | mutation | `listId`, `name`, `email` | a manual member = the person asked Ariel directly; a lead with that email gets consent = true |
| `lists:removeMember` | mutation, `--yes` | `memberId` | |
| `lists:unsubscribe` | mutation, `--yes` | `email`, `listId?` | the recipient's opt-out; withdraws the lead's consent |
| `lists:enrollLead` | mutation | never from the CLI | the sign-up gate |

Member statuses: `subscribed` (mailed), `pending_consent` (visible, never mailed), `unsubscribed`.
Sources: `lead` (ticked on the site), `manual` (asked Ariel).

## campaigns

| function | kind | args | notes |
|---|---|---|---|
| `campaigns:listCampaigns` | query | | newest first with `listName` |
| `campaigns:getCampaign` | query | `campaignId` | with `list: {_id, name, subscribed}` |
| `campaigns:deliveriesFor` | query | `campaignId`, `paginationOpts`, `status?` (`sent`, `failed`) | |
| `campaigns:deliveredEmails` | query | `campaignId` | addresses already sent |
| `campaigns:createCampaign` | mutation | `listId`, `subject` (≤150), `preheader?` (≤200), `bodyMarkdown` (≤60,000), `advertisement` (bool: "פרסומת" prefix) | a draft |
| `campaigns:updateCampaign` | mutation | `campaignId` + the same fields | drafts only |
| `campaigns:deleteCampaign` | mutation, `--yes` | `campaignId` | drafts and failed only |
| `campaigns:markSending`, `recordDeliveries`, `markSent`, `markFailed`, `markTestSent` | mutation | never from the CLI | the send loop in the Next server |

Sending and the test send happen only from `/admin/campaigns/<id>` in the browser (the Resend key lives
in the Next server).

## settings

| function | kind | args | notes |
|---|---|---|---|
| `settings:listSettings` | query | | `[{key, value, updatedAt}]` |
| `settings:getSetting` | query | `key` | |
| `settings:setSetting` | mutation | `key`, `value` (any JSON) | logs `setting`. `--yes` when it opens the gate (`guidesGate` → `{enabled:false}`) or sets `mailing.autoEnroll` to `all` |

Known keys: `guidesGate` `{enabled: boolean}` (default on); `mailing.senderAddress` (string, printed in
every campaign); `mailing.autoEnroll` (`consenting` default, or `all`).

## voice (Jarvis's re-recorded lines)

| function | kind | args | notes |
|---|---|---|---|
| `voice:listVoiceLines` | query | | every admin take: lineId, text, mime, bytes, durationSec, voice, model, updatedAt, url |
| `voice:voiceManifest` | query (public) | | what visitors' players read |
| `voice:saveVoiceLine` | mutation, `--yes` | `lineId`, `text`, `storageId`, `mime`, `bytes`, `durationSec`, `voice`, `model` | stores a take (the previous file is deleted). Recording itself: the CLI's `record-voice` (session). |
| `voice:deleteVoiceLine` | mutation, `--yes` | `lineId` | the repo take plays again |

## adminLog

| function | kind | args | notes |
|---|---|---|---|
| `adminLog:listLog` | query | `limit?` (≤200, default 50) | newest first: `action`, `detail`, `at` |
| `adminLog:log` | mutation | `action`, `detail` | write your own note (e.g. `agent.note`) |

Action codes: `guide.create|update|delete|files|reorder|publish|unpublish`, `bundle.publish|unpublish`,
`lead.consent|delete|export`, `message.delete`, `content.save|delete|restore`, `voice.record|delete`,
`media.upload|update|delete`, `mailing.list.create|update|delete`, `mailing.members.add`,
`mailing.member.remove`, `mailing.unsubscribe`, `mailing.campaign.create|update|delete|send|sent|failed|test`,
`category.create|update|rename|delete|reorder|seed`, `setting`.
