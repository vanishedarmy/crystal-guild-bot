# Crystal Guild v1.8.0 RC1 — Merc Service

## Deployment lifecycle hardening

- A Merc reservation changes to **Deployed** when its matching Hunt, Venture, or Raid actually begins.
- The deployed Hero and mission slot remain unavailable until that assignment resolves.
- Deployed contracts cannot be cancelled or reused mid-mission.
- Hunt, Venture, and Raid continue to resolve independently; one completed assignment does not consume either of the other two slots.

## Recovery and failure safety

- Timed Hunt deployment survives runtime checkpoint/restart recovery and still blocks rehire after recovery.
- If Solo Venture setup fails before a playable assignment begins, the paid Merc reservation is restored rather than consumed.
- Existing Alpha 2 reservations and deployments remain compatible.

## Balance and compatibility

- Hunt Seal fees remain Aerith 5, Tifa 6, Zidane 5, Yuna 7, Balthier 9, Cloud 12.
- Hero signature effects are unchanged.
- Local DB schema remains **17**.
- Hosted sync remains **1**.
- Portal Action protocol remains **34**.
- No player reset is required.
