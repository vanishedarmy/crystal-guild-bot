Crystal Guild v1.2.0 — Expeditions Beta 4 Bot
Runtime: 1.2.0-expeditions-b4
Local DB schema: 8
Hosted sync schema: 1
Portal Action protocol: 20

Beta 4 is the release-hardening checkpoint. Persistent Expeditions/Wayfarer runs now block passive Long Rest and stream-live resource refreshes, and persistent Adventure Portal mutations commit gameplay state plus replay receipts atomically. Restart recovery, schema-7 → schema-8 migration continuity, duplicate-reward protection, database integrity, stress tests, and release packaging are validated before RC1. No player reset or new environment variable is required.
