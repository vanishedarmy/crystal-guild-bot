# Crystal Guild Alpha 13 Trading Post — Matching runtime requirements

Current Bot/Web release: `1.9.0-trading-post-qol-alpha13`. Portal Action protocol **39**, local Bot schema **25**, hosted sync **1**. Preserve existing tokens, databases and environment secrets. Follow `START_HERE.md`.

# Portal Actions — Alpha 8

Portal Action protocol **37**. Deploy the paired `1.9.0-seasonal-events-alpha8` Bot/Web packages; preserve current OAuth/session keys and private sync configuration.

Authenticated Portal mutations are queued and verified by the authoritative Bot (including gear favorites, Trading Post operations and seasonal event shop/state actions). Repeated requests use the existing idempotency receipts. Do not expose private Bot tokens, database files or secrets to the public frontend.

The cleanup hotfix makes **no protocol or gameplay change**.
