# Validation Report — Crystal Guild v1.7.1 Resynthesis Alpha 2 Hotfix 1

**Result: PASS**

## Release contract
- Bot runtime: `1.7.1-resynthesis-a2h1`
- Paired Web frontend: `1.7.1-resynthesis-a2` (unchanged from Alpha 2)
- Local DB schema: **15**
- Hosted sync schema: **1**
- Portal Action protocol: **32**
- Twitch command prefix: `!`
- Baseline: v1.7.1 Resynthesis Alpha 2

## Regression
- Bot: **681 / 681 PASS**
- Frontend: **562 / 562 PASS**
- Hosted Web/API: **65 / 65 PASS**
- Bot Python parse/compile: **120 / 120 PASS**
- Web Python parse: **16 / 16 PASS**
- JS/MJS syntax: **205 / 205 PASS**
- CSS files structurally present: **8 / 8**
- WebP decode: **843 / 843 PASS**
- Public PNG count: **0**

## Encounter variety regression
- Whispering Caverns Lv.25 Solo Venture no longer collapses to Magic Pot alone.
- Solo Venture widens a narrow preferred band to at least five valid monsters whenever the region can provide them.
- Immediate repeats are reduced to 10% of normal effective weight.
- A third identical encounter is blocked whenever an alternative candidate exists.
- A single monster is capped to approximately 45% effective weight when 3+ candidates exist.
- Region rarity tables, rewards, drops, enemy levels, Rally +10 cap, Solo +5 cap, and all Gold Saucer Alpha 2 balance remain unchanged.

No database migration or player reset is required.
