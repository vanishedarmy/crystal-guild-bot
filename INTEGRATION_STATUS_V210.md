# Crystal Guild v1.9.97.7 — Bot V2.10: Beastmaster Companion Ownership

Built directly on the V2.9 integrated Bot source. This is a **source integration candidate**, not an automatically deployed production release.

## Implemented
- SQLite schema 29: `beastmaster_companions` with player/monster ownership and a unique active pet per player.
- 23 curated tameable species from the existing monster catalog; bosses, raid marks and quest guardians are excluded via an allow-list.
- An eligible Beastmaster (job Lv30+ and at least the creature level) can tame a species after **3 recorded Bestiary defeats**.
- Up to **5 owned species** per player. `!pets`, `!tame <species>`, `!petselect <species>`, `!petrelease <species>` are connected to Twitch.
- Roster data survives SQLite restart, and the migration from a real V2.9 schema-28 save was exercised without losing player, job or Bestiary records.
- Active encounters (venture/hunt/world event using the shared combat loop) and raids now snapshot the **selected, owned** companion from the database when combat starts. The selected companion assists on `Call Beast` and `King of Beasts`.
- Companion contribution: +2% to +8% damage by species level. An equipped Beastmaster Relic adds `Pack Coordination` and, against raid bosses, `Alpha Pact`; these traits **do not** enhance generic Call Beast strikes without an owned companion.
- Existing Call Beast and King of Beasts remain fully usable without a tamed creature. No existing item IDs, Relic stages or monster stat records were changed.

## Important limitations
- This phase does NOT create independent turn-taking pet entities, companion HP, XP, healing, separate actions, AI behavior or pet portraits. The companion is a persisted owner-selected **assistant to the existing two Beastmaster abilities**.
- Pet selection is snapshotted at combat start; switching pets during an ongoing encounter applies on the next encounter (not mid-round).
- Solo expeditions, dungeon battle resolvers and all quest-specific combat loops have not been wired to companion assists. Raid and shared active encounters are covered.
- The player-facing Web/Portal companion screen and Player Guide have not been synchronized.
- The V2.9 Bot and original uploaded ZIP were not modified. Back up production Bot + DB, test on an isolated copy before deployment.

## Release and safety
- `VERSION.txt` remains `1.9.97.7-regional-progression` to avoid claiming a new published release; V2.10 is an integration candidate label.
- Automatic SQLite pre-migration backup is created for existing player databases before schema 29.
- `!petrelease` is permanent until the creature is tamed again; it never removes Bestiary victories.
- When installing, use **either** the full Bot ZIP **or** the V2.10 merge patch on an already installed V2.9 Bot.

## Test coverage
- 15 new V2.10 unit tests, 55 Relic tests, 24 shared active-battle tests, 10 raid tests, 3 resource tests = **107 passed**.
- Separate real V2.9 → V2.10 database migration smoke test passed.
- Python compileall and ZIP integrity verification passed.
- This is selected regression coverage, not an entire-project test-suite run or live Twitch integration test.
