> **v2.1.0 Activity Resolution Hotfix (November 4, 2026):** Deploy matching Bot and Web together. Portal Action protocol is now **40** (previously 39); timed Hunts have automatic overdue recovery plus a safe **Finish Hunt** action. No database migration or new artwork is required. See `INSTALL_ACTIVITY_RESOLUTION_V210.md` in the release root. Older version/protocol references below are historical.

# Crystal Guild v1.9.7 — Portal Actions Setup

Current matching Bot/Web release: `1.9.7-queens-blood`. Portal Action protocol **39**, local Bot schema **27**, hosted sync schema **1**. Preserve tokens, databases, private sync configuration, and session secrets. Follow `README_FIRST.txt` for current deployment instructions.

## Historical compatibility notes

# Crystal Guild Alpha 13 Trading Post — Matching runtime requirements

Current Bot/Web release: `1.9.0-trading-post-qol-alpha13`. Portal Action protocol **39**, local Bot schema **25**, hosted sync **1**. Preserve existing tokens, databases and environment secrets. Follow `START_HERE.md`.

# Portal Actions — Alpha 8

Portal Action protocol **37**. Deploy the paired `1.9.0-seasonal-events-alpha8` Bot/Web packages; preserve current OAuth/session keys and private sync configuration.

Authenticated Portal mutations are queued and verified by the authoritative Bot (including gear favorites, Trading Post operations and seasonal event shop/state actions). Repeated requests use the existing idempotency receipts. Do not expose private Bot tokens, database files or secrets to the public frontend.

The cleanup hotfix makes **no protocol or gameplay change**.
