# Web Sync — Crystal Guild v1.7.0 Retainer Service Alpha 1

Hosted sync schema remains **1**. Portal Action protocol advances to **30** for Retainer Service.

New Portal actions:
- `RETAINER_STATE` — no payload
- `RETAINER_DISPATCH` — `{ "assignment": "<assignment_id>" }`
- `RETAINER_COLLECT` — no payload

The Bot remains the authoritative writer. Retainer dispatch/collection is Portal-only and does not post routine activity to Twitch chat. Deploy the matched Alpha 1 Bot and Web together.
