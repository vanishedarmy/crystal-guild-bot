# Portal Actions — Crystal Guild v1.7.0 Moogle Retainer

Portal Action protocol is **31**.

Retainer actions:
- `RETAINER_STATE` with `{}`
- `RETAINER_DISPATCH` with `{ "assignment": "<assignment_id>", "priority": "<optional_material_id>" }`
- `RETAINER_COLLECT` with `{}`

Valid assignment IDs are `field_gathering`, `monster_salvage`, `mineral_survey`, `regional_procurement`, and `specialist_acquisition`. The optional `priority` must be empty/omitted or match a material offered by the selected route. Hosted validation rejects unknown fields, malformed material IDs, and unknown assignment IDs. The local Bot performs all authoritative Gil, timer, reward, inventory, Retainer EXP, history, and exactly-once settlement work.
