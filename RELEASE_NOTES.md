# Crystal Guild v1.9.0 Alpha 5 — Title Status Hardening

Alpha 5 hardens the achievement and Title pipeline introduced in Alpha 3. Existing heroes are proactively reconciled against the current catalog, reward Titles self-repair if an older achievement row exists without its Title, and the Portal now presents permanent unlocks consistently even when the underlying requirement is a reversible value such as current Gil or inventory held.

## Achievement and Title hardening
- The Bot performs a safe, idempotent achievement/Title reconciliation for all existing heroes at startup.
- In-process hosted Portal sync reconciles a hero immediately before publishing that hero's snapshot.
- Already-unlocked achievements now repair a missing reward-Title row automatically. This covers future cases where a Title reward is added after the achievement already existed.
- Achievement evaluation runs to a fixed point, so dependency rewards such as **Golden Saucer** can unlock in the same cycle even if catalog ordering changes.
- Permanent achievements always display as complete after unlock. If a reversible value later drops below the original target, the Portal still shows 100% completion rather than a contradictory partial bar.
- Portal progress calculation now mirrors the Bot for Expedition region progress and the full supported requirement family, preventing false zero-progress displays.
- Secret achievements remain hidden until earned; no secret conditions were exposed.

## Carried forward unchanged
- All Alpha 3 Title requirements and rewards, including **Oh hi Mark.**, remain unchanged.
- Alpha 4 Navigation Accessibility remains fully active.
- Alpha 2 economy balance and Gold Saucer payout tuning remain unchanged.
- Trading Post, Merc Service, Fellowship, Retainers, Resynthesis, inventory/equipment, and all gameplay rewards remain unchanged.

## Compatibility
- Runtime/frontend: `1.9.0-title-status-hardening-alpha5`
- Local schema: **19**
- Hosted sync schema: **1**
- Portal Action protocol: **36**
- No database migration or player reset is required.
