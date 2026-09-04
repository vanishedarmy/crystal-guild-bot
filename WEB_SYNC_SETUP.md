# Web Sync — Crystal Guild v1.7.1 Resynthesis Alpha 2 Hotfix 1

Hosted sync schema remains **1**. Portal Action protocol is **32**.

Retainer Portal actions:
- `RETAINER_STATE` — no payload
- `RETAINER_DISPATCH` — `{ "assignment": "<assignment_id>", "priority": "<optional_material_id>" }`
- `RETAINER_COLLECT` — no payload

`priority` may be omitted or sent as an empty string for a general mixed haul. When supplied, it must be a material offered by the selected assignment route. The Bot remains the authoritative writer. Routine Retainer dispatch/collection remains Portal-only and does not post to Twitch chat.

Deploy the v1.7.1 Resynthesis Alpha 2 Hotfix 1 Bot with the unchanged v1.7.1 Resynthesis Alpha 2 Web build.
