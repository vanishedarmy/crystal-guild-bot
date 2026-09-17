# Crystal Guild v1.8.0 Alpha 2 — Merc Service Balance Audit

## Scope
Alpha 2 audits Hero Merc Service against the established Hunt Seal economy and improves Portal clarity without changing Merc combat signatures, local schema, hosted sync, or Portal Action protocol.

## Hunt Seal earning curve
Authoritative Hunt data currently pays:

| Hunt rank | Seal range | Average |
| --- | ---: | ---: |
| C | 3–10 | 6.4 |
| B | 18–24 | 21 |
| A | 40–50 | 45 |
| S | 80–100 | 90 |

Relic progression remains a much larger Seal sink, with common stage costs of 40 / 90 / 220 Hunt Seals.

## Merc fee tuning
Alpha 1 / Hotfix 3 fees were inexpensive enough that premium Merc utility could become nearly incidental once B-rank Hunts were routine. Alpha 2 uses a modest increase rather than a major economy reset:

| Hero | Alpha 1 fee | Alpha 2 fee | Reason |
| --- | ---: | ---: | --- |
| Aerith | 4 | 5 | Strong recovery + Regen, still entry-accessible |
| Tifa | 5 | 6 | Reliable burst damage on Hunt/Raid |
| Zidane | 4 | 5 | Guaranteed additional drop, weighted toward normal loot |
| Yuna | 6 | 7 | Recovery + Protect utility |
| Balthier | 7 | 9 | Opening shot plus rare-spoil attempt |
| Cloud | 10 | 12 | Highest unlock tier and strongest opening burst |

The goal is that entry Mercs remain approximately one C-rank Hunt, while B/A/S Hunts comfortably fund premium contracts without making the existing Quartermaster/Relic Seal sinks irrelevant.

## Signature effect audit
No signature-effect nerfs or buffs were necessary in this pass:

- Cloud / Tifa remain differentiated by heavy vs faster/lighter opening burst.
- Aerith emphasizes recovery + Regen.
- Yuna trades raw recovery for Protect.
- Zidane guarantees one extra drop, but weighted selection favors ordinary drop chances rather than always forcing the rarest item.
- Balthier has a smaller opening shot plus a probabilistic rare-spoil attempt rather than guaranteed rare loot.

## UX audit
Alpha 2 adds:

- a visual three-slot deployment board for Hunt / Venture / Raid;
- explicit open vs assigned slot state;
- quick jump from each slot to that mission roster;
- exact per-Hero availability reasons for the selected mission;
- clear On Contract / progression Locked / unsupported job / occupied slot distinctions;
- no automatic forced switch away from a filled job tab, so players can inspect why the roster is unavailable.

## Release contract
- Runtime/frontend: `1.8.0-merc-a2`
- Local schema: **17**
- Hosted sync: **1**
- Portal Action protocol: **34**
- Player reset: **No**
