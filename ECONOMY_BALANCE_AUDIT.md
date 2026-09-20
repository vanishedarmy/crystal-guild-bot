# Crystal Guild v1.9.0 Alpha 2 — Economy Balance Audit

## Goal
Keep progression rewarding and sustainable without turning Crystal Guild into a grind. The audit favors targeted corrections over blanket nerfs: normal play should remain generous, while deterministic resale loops and clearly under-rewarding activities are corrected.

## Executive result
**PASS after targeted corrections.** The core Gil curve, shop progression, Hunts, Raids, daily income, Trading Post fees, and most of the Gold Saucer economy are already healthy. Four targeted changes are warranted:

1. Remove two passive Retainer-to-NPC profit loops.
2. Remove the Workshop Mythril → Adamantite → NPC profit loop.
3. Make Monster Toss materially less punishing while retaining a daily cap.
4. Replace the Trading Post's inaccessible Level-1 Expedition gate with 15 Ventures.

No player reset or database migration is required. Local schema remains **19**, hosted sync remains **1**, and Portal Action protocol remains **36**.

## Core Gil economy — KEEP

### Daily Gil
- Base daily Gil: **125**.
- +**8 Gil per player level**, with bounded variance.
- Hard daily cap: **1,000 Gil**.

This remains a useful floor without replacing active play.

### NPC resale ratios
- Materials: **70%**.
- Gear: **50%**.
- Consumables: **40%**.

These preserve the usefulness of gathered materials while preventing ordinary shop buy/sell loops.

### Hunts and Raids
- Repeat Hunts retain only **80%** of first-clear Gil and **85%** of progression rewards.
- Raid Gil is a **fixed shared pool**, not a per-player multiplier, so larger groups do not multiply currency creation.

No reductions are recommended.

### Shop affordability
Representative shop gear remains around **6–14 same-level monster Gil payouts** before counting item drops, Hunts, daily Gil, Ventures, or other rewards. That is an appropriate baseline: a player should not need dozens of repetitive kills just to replace one ordinary piece of gear.

### Trading Post
- Listing fee: **2%**.
- Completed-sale tax: **5%**.
- Duration: **48 hours**.
- Active listing cap: **24**.

These are meaningful Gil sinks without making player trading feel punitive. **No fee increase is recommended.**

## Retainer Service — CORRECTED
Retainers are meant to be a convenience route for materials, not a passive Gil printer. Expected NPC liquidation includes normal reward quantities and the rank-based bonus-find chance.

| Assignment | Expected NPC liquidation | Old cost | New cost | New liquidation/cost |
|---|---:|---:|---:|---:|
| Field Gathering | ~90.85 | 100 | 100 | 90.9% |
| Monster Salvage | ~241.54 | 250 | 250 | 96.6% |
| Mineral Survey | ~794.36 | 500 | **850** | 93.5% |
| Regional Procurement | ~857.71 | 900 | 900 | 95.3% |
| Specialist Acquisition | ~1,759.22 | 1,500 | **1,850** | 95.1% |

Focused dispatches remain optional convenience premiums:
- Mineral Survey focused: **625 → 1,050 Gil**.
- Specialist Acquisition focused: **1,875 → 2,300 Gil**.

These changes close passive resale loops without reducing the materials players receive.

## Fellowship Workshop — CORRECTED
Workshop exchanges are explicitly intended to be lossy convenience conversions. One exchange violated that rule.

| Exchange | Input NPC opportunity value | Fee | Output NPC sale value | Immediate flip result |
|---|---:|---:|---:|---:|
| Refine Mythril | 155 | 250 | 182 | -223 |
| Temper Dragon Scale | 948 | 300 | 909 | -339 |
| Press Adamantite | 1,092 | **1,600** | 2,660 | **-32** |
| Condense Dark Matter | 3,640 | 1,000 | 3,500 | -1,140 |

**Press Adamantite fee: 750 → 1,600 Gil.** Adamantite's base value is deliberately left unchanged so gatherers, crafters, and Trading Post sellers are not punished for a Workshop-specific exploit.

## Fellowship Trading Post unlock — ACCESSIBILITY FIX
The Trading Post is a **Fellowship Level 1** building, but its original requirement asked for **15 Fellowship Expeditions**. The Expedition Board itself does not become available until **Fellowship Level 6**, making the Level-1 Trading Post effectively inaccessible until much later.

Corrected requirement:
- Fellowship Level **1**.
- **25,000 Gil**.
- **3 Mythril Ore**.
- **15 completed Ventures**.

This preserves the intended activity requirement while making the Trading Post genuinely early-Fellowship content.

## Gold Saucer economy
Gold Saucer remains isolated from Gil and its prizes are cosmetic titles. The audit therefore focuses on MGP pacing and whether any attraction feels mandatory or unrewarding.

### Daily floor — KEEP
- Welcome purse: **500 MGP**.
- Daily recovery allowance after the welcome day: **125 MGP**.
- Daily reward: **50 MGP**.
- Normal returning-player floor: **175 free MGP/day**.

This prevents unlucky players from being locked out and strongly reduces grind pressure.

### Mini Cactpot — KEEP
- Entry: **10 MGP**.
- Jackpot: **1,250 MGP**.
- Random-line expected payout: about **39.17 MGP**.
- Limited to once per day.

The game is generous but highly bounded and appropriately feels like a daily event.

### Crystal Slots — KEEP
- Entry: **15 MGP**.
- Exact theoretical return: about **97.145%**.

Slots remain a repeatable soft sink rather than a farming engine.

### Monster Toss — BUFFED
Old payouts made several sensible beginner choices severe MGP traps; a perfect Small Pot / Safe Throw game could score below the first payout threshold and receive **0 MGP**.

New payout tiers:
- 75 points: **10 MGP**.
- 100 points: **15 MGP**.
- 250 points: **30 MGP**.
- 400 points: **50 MGP**.
- 600 points: **80 MGP**.
- 900 points: **120 MGP**.

Entry remains **20 MGP**, five throws per game, three games per UTC day.

Expected fixed-strategy payout now ranges from roughly **9.8 MGP** for the safest low-value approach to **37.9 MGP** for the strongest high-risk profile. The best expected net is about **+17.9 MGP/game**, capped at three games daily. This makes performance matter without allowing Monster Toss to dominate the Saucer economy.

### Chocobo Racing — KEEP
Three races per day and course-specific entry costs already bound the faucet. Podium rewards remain meaningfully profitable, particularly for players who have invested in Chocobo progression. No reduction is recommended.

### Triple Triad — KEEP
Triple Triad is the most skill-rewarding MGP activity, but it is limited to **five matches/day**, stronger opponents require wins to unlock, and its rewards are still confined to cosmetic MGP progression. Reducing it would primarily make prestige-title acquisition grindier, so the current **100 / 150 / 240 MGP** win purses are retained.

### Prize Counter — KEEP
Current purchased title range: **500–9,000 MGP**.

At the free 175-MGP daily floor, the most expensive title would take roughly 52 days with no gameplay at all. Active Gold Saucer play shortens that substantially; a regular player engaging with Cactpot, Racing, Toss, and/or Triad should reach prestige purchases on the scale of roughly **one to two weeks**, not months.

This is the intended pacing. New achievement/secret titles should reduce pressure to purchase every title rather than forcing Prize Counter prices downward.

## Long-term sinks — WATCH, NOT CHANGED
Permanent Elite Merc contracts and high-tier Fellowship projects are intentionally large one-time sinks. They should remain aspirational, but future live economy reports should be checked for actual median time-to-afford before raising any of them further.

## Regression guardrails added
- Every Retainer assignment's expected NPC liquidation must remain below its normal dispatch fee.
- Every Workshop material exchange must cost at least as much as immediate NPC liquidation of the output relative to the inputs surrendered.
- Monster Toss's best fixed strategy remains daily-bounded while the low-score floor now pays something.
- Trading Post Level-1 construction explicitly requires Ventures rather than inaccessible Expeditions.

## Balance philosophy going forward
1. Do not nerf healthy faucets merely because a new sink exists.
2. Correct deterministic arbitrage at the conversion point that causes it.
3. Use daily limits for high-fun/high-payout side activities instead of making rewards stingy.
4. Judge prices by **time-to-afford**, not by how large the number looks.
5. Ordinary upgrades should be reachable through normal play; only prestige and permanent unlocks should require long-term saving.
