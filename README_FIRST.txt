CRYSTAL GUILD v1.1.16 — ARSENAL HOTFIX 4
========================================

Upgrade baseline: v1.1.16 — Arsenal Hotfix 3

Streamer adventure-recovery hotfix:
- adds owner-only !clearadventures (alias !clearventures);
- clears the shared field/Rally encounter, every timed Hunt assignment, and every persisted Solo Venture;
- works entirely from the authoritative Bot backend, so it can recover a Solo Venture even when Portal cannot render it;
- preserves player progression, inventory, current persisted HP/MP/AP, cooldowns, camps, shops, achievements, and titles;
- deliberately leaves raids/world bosses untouched;
- immediately wakes hosted Portal sync after a streamer clear.

Bot runtime: 1.1.16-arsenal-h4
Matching Web asset revision: 1.1.16-arsenal1h4
Local DB schema: 5 (unchanged)
Hosted sync schema: 1 (unchanged)
Portal Action protocol: 14 (unchanged)

This is a matching Bot + Web update because the authoritative Twitch command lives in the Bot and its reference lives on the Streamer Dashboard. No database migration, player reset, new Render secret, or OAuth change is required.
