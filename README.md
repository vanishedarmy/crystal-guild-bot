# Crystal Guild v1.2.0 — Expeditions Beta 4

Beta 4 freezes gameplay/content and hardens the v1.2 release path. Persistent Solo/Expedition runs retain HP/MP/AP pressure through Long Rest and stream-start refresh events, while persistent Adventure Portal mutations now commit their gameplay writes and replay receipt in one SQLite transaction so acknowledgement retries cannot duplicate rewards or stage progress.

Runtime `1.2.0-expeditions-b4` · local DB schema **8** · hosted sync schema **1** · hosted sync compatibility `1.1.15-wayfarer` · Portal Action protocol **20** · Twitch prefix `!`.

Use `python run_maintenance.py --recovery-drill` for the non-destructive backup/restore drill and `python run_stress_test.py` for the synthetic concurrency/integrity test. The bundled release validation also covers persistent Expedition restart recovery and the direct pre-v1.2 schema-7 → schema-8 migration path.
