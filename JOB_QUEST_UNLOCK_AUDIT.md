# Job Quest Unlock Audit — v1.7.1 Resynthesis Alpha 2 Hotfix 2

## Root cause

The requirement counters were not lost. Character/Job levels, Hunts, Bestiary defeats, Ventures, Masteries, and quest prerequisites were already stored correctly. The lock occurred because advanced Jobs that require `quest_complete` only considered the quest complete after an explicit `!quest <name>` claim. The hosted Portal exposes live Job switching but has no generic Job Quest claim action, so a qualified player could remain locked indefinitely behind an unclaimed quest row.

## Repair

- Ready Job Quests self-reconcile when `!job`, `!jobinfo`, `!quests`, or Portal `CHARACTER_STATE` is requested.
- Existing progress is evaluated retroactively; no milestone needs to be repeated.
- Quest rows are inserted exactly once under an authoritative write transaction.
- Gil transactions and quest titles are granted exactly once with the quest completion.
- Quest-count achievements are re-evaluated after the repair.
- The existing advanced-Job requirement evaluator then sees `quest_complete` normally; no separate unlocked-job table or schema change is introduced.
- Manual `!quest <name>` remains supported and uses the same completion path.

## Regression coverage

- Existing manual Oath of Light → Paladin unlock test remains passing.
- New direct Job-switch test proves an already-qualified Abyssal Oath is repaired retroactively and Dark Knight becomes selectable.
- Repeated Job changes prove quest Gil is not duplicated.
- New Portal `CHARACTER_STATE` test proves Oath of Light is reconciled on Jobs-state load, Paladin is returned unlocked, and a second refresh grants nothing again.

## Compatibility

Bot runtime `1.7.1-resynthesis-a2h2`; paired Web remains `1.7.1-resynthesis-a2`. Local schema 15, hosted sync 1, Portal Action protocol 32. No migration or player reset.
