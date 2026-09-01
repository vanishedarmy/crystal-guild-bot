# Crystal Guild v1.7.0 — Retainer Service Alpha 1

Retainer Service adds a personal procurement agent to the Adventurer Portal. Pay Gil to dispatch one Retainer on timed material-gathering assignments, then collect the committed crafting-material haul when the Retainer returns.

Alpha 1 includes five procurement assignments, Retainer Rank/EXP progression, small bonus-find chances, restart-safe persistent assignment state, and exactly-once reward collection. Retainers do not store equipment, enter combat, or replace the player's inventory.

Database schema advances from 13 to **14** and Portal Action protocol advances from 29 to **30**. Existing player data is preserved in place with the normal verified pre-migration backup. Gold Saucer v1.6.0 systems and balance are unchanged.

Runtime identity: `1.7.0-retainer-a1`.
