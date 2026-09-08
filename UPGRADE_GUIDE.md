# Upgrade — Hotfix 5 Treasure Seekers Solo Progress

This is a **Bot-only logic correction** on top of the finalized Hotfix 5 Armor Best Use & UI Corrections package. The paired Web package does not change.

Preserve the live `crystal_guild.db`, token database, persistent storage, and environment secrets. **No database migration** is required; schema remains **15** and Portal protocol remains **32**.

Deploy either the full Bot archive or the Bot incremental patch, then restart the Bot. Existing player progression, Fellowship state, current weekly-order progress, Gold Saucer state, Retainers, inventory, Jobs, Resynthesis, and all other persistent systems remain intact.

Verification after restart:
1. Confirm `!cgversion` reports `1.7.1-resynthesis-a2h5`.
2. Find a treasure chest through Solo Venture.
3. Reopen Fellowship Orders and confirm **Treasure Seekers** advances by exactly **1**.
4. Repeating/retrying the same Portal action must not advance it a second time.
5. Rally information remains **100% Encounter / 0% Treasure Chest** and Solo Venture remains **80% / 20%**.

Historical Solo treasure discoveries are not retroactively assigned to the current weekly order because the pre-fix aggregate statistic cannot establish which order week each chest belonged to.
