# Crystal Guild v1.4.0 — Dungeons & Delves

## Production release

Dungeons & Delves promotes the fully hardened RC1 feature set unchanged into production. No new Dungeon content, reward tuning, economy, combat balance, schema, or Portal protocol change is introduced by the promotion itself.

### Shipped feature set
- Four persistent Dungeons with Expedition-based unlocks and distinct reward/encounter identities.
- Chamber types include combat, treasure, hazards, sanctuaries, Crossroads, weighted Events, minibosses, and bosses.
- Route decisions can affect later hazards, enemies, or combat rewards.
- Player-paced combat supports Attack, Job Ability, Item, and Defend with persistent HP/MP/AP and inventory use.
- Dungeon Cache settles at 100% on clear, 50% on retreat, and 25% on defeat.
- First-clear bonuses and personal Dungeon records use existing progression without another currency.

### Reliability
- Every Dungeon mutation is bound to exact run ID + chamber ID + persisted revision.
- State-guarded writes serialize at SQLite write intent before the authoritative state read, including across separate Bot/database connections.
- Duplicate action IDs replay one committed result and never advance twice.
- Active runs, route effects, action receipts, and progress survive restart/reconnect.
- Mobile Dungeon Board disclosure remains right-aligned with right-hand closed / down-hand open states.

### Compatibility
- Runtime: `1.4.0-dungeons-delves`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch prefix: `!`

RC1 → production requires no DB migration, reset, OAuth/environment change, or new environment variable. Deploy matching production Web + Bot together.
