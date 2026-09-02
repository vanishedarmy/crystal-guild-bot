# Web Sync — Crystal Guild v1.7.0 Moogle Emporium Annex Alpha 3

Hosted sync schema remains **1**. Portal Action protocol advances to **31** for targeted Retainer procurement.

Retainer Portal actions:
- `RETAINER_STATE` — no payload
- `RETAINER_DISPATCH` — `{ "assignment": "<assignment_id>", "priority": "<optional_material_id>" }`
- `RETAINER_COLLECT` — no payload

`priority` may be omitted or sent as an empty string for the Alpha 1 general mixed-haul behavior. When supplied, it must be a material offered by the selected assignment route. The Bot remains the authoritative writer. Retainer dispatch/collection is Portal-only and does not post routine activity to Twitch chat. Deploy the matched Alpha 2 Bot and Web together.
