Crystal Guild v1.9.0 Alpha 12 — Camp & Recovery
Runtime: 1.9.0-camp-recovery-alpha12 | local SQLite schema 24 | hosted sync 1 | Portal Action protocol 38

This Bot release adds persisted meal/preparation state and Solo Venture-only bonus snapshots. New craftable and purchasable Trail Rations, three free preparations, and existing timed Camp/Potion/Tent remain server-authoritative. No equipment durability changes. Existing Alpha 11 mobile combat and Alpha 10 Records & Moments are preserved.

Pair this Bot with the same Alpha 12 Web source and Web/frontend/public. Back up live state and credentials before deployment; the 23→24 migration makes a verified backup before changing schema. Run the database integrity/recovery drill on a copy before staging. See RELEASE_NOTES.md and UPGRADE_GUIDE.md.
