# Crystal Guild v1.6.0 — Gold Saucer RC2 Manual Check

- [ ] `!cgversion` reports `1.6.0-gold-saucer-rc2`.
- [ ] Existing player MGP balance, Prize Counter ownership, Triple Triad collection/deck, and Gold Saucer records survive the upgrade unchanged.
- [ ] Mini Cactpot, Crystal Slots, Monster Toss, Chocobo Racing, and Triple Triad are all playable from the Gold Saucer tab.
- [ ] Starting Monster Toss immediately changes its daily counter from 0/3 to 1/3 before the fifth throw resolves.
- [ ] Starting Triple Triad immediately changes its daily counter from 0/5 to 1/5 before the board resolves.
- [ ] A Toss/Triad session started before 00:00 UTC and finished after midnight remains charged to the prior UTC entry day.
- [ ] Triple Triad shows the complete printed 3:4 card faces with no duplicate stat/name overlay; captures use the values printed on the art.
- [ ] Saucer Attendant, Card Shark, and Crystal Master use their compact opponent cards; the removed wide Choose Opponent banner does not return.
- [ ] Mini Cactpot and Crystal Slots remain permanently open. Monster Toss, Chocobo Racing, Triple Triad, Prize Counter, Saucer Ledger, and Recent Activity use shared finger-pointer collapse controls.
- [ ] Moogle Emporium Buy/Sell, Blacksmith quantity, and Fellowship Workshop quantity inputs allow typing `5` over the starter `1` on desktop and mobile.
- [ ] Refresh/reconnect during active Monster Toss and Triple Triad restores the same authoritative session instead of rerolling/restarting it.
- [ ] Retrying a completed Portal action cannot duplicate an MGP charge, payout, Triple Triad move/card reward, or Prize Counter purchase.

## Legacy regression checklist

# Crystal Guild v1.1.17 — Arsenal II Manual Check

- [ ] `!cgversion` reports `1.1.19-retro-phase-iii-rc1`.
- [ ] `!streamstatus` still reports LIVE/OFFLINE correctly.
- [ ] Start/join a Raid while live; `!attack` queues for the next Raid round.
- [ ] `!ability <name> [target]` queues and resolves, spending MP/AP only on resolution.
- [ ] `!defend` resolves as a Raid action, restores defensive MP/AP, and reduces that round's incoming boss damage.
- [ ] `!use <item> [target]` queues and only consumes the item when the effect successfully resolves.
- [ ] A living Raider who submits no command defaults to Attack so the Raid cannot stall.
- [ ] A queued action can be replaced by another action before the round closes.
- [ ] A killing-blow ability persists its MP/AP spend before the Raid clears.
- [ ] Existing `!limit`, `!summon`, Raid rewards, Raid timers, and auto-resolution remain functional.
- [ ] `!daily` randomized provisions and `!substatus` subscriber-tier behavior from Hotfix 2 remain intact.
- [ ] Existing player progression, Fellowship, Adventure Board, hosted overlay, and stream-live gate remain intact.
- [ ] On the Portal, an active Rally Venture renders inside the Rally Venture panel, not below Current Region.
- [ ] Portal buttons/filters are readable, identify their purpose/target, and remain clear when selected, focused, or disabled.

## Arsenal content

- [ ] Each Job detail shows six active abilities at JLv.1 / 8 / 15 / 22 / 30 / 40.
- [ ] Element/special-effect traits appear in Job details, Player Guide, and Solo Venture ability selection.
- [ ] Hunts include starter marks at Lv.2 / 4 / 6 / 8 in ascending order.
- [ ] World Boss data includes Goblin King, Hornet Empress, Skeleton Warlord, and Gigas Chief before Bomb King.
- [ ] Blacksmith/crafting references include the eight new Lv.3–15 consumable recipes.

## Arsenal Hotfix 1 — timed Hunts

- [ ] A new C/B/A/S Hunt shows an expected return of 5m / 15m / 30m / 1h respectively; S+ support uses 2h when an S+ mark exists.
- [ ] Starting a Hunt does not create a shared Active Battle or ask for `!attack`, `!ability`, `!defend`, or `!use` round input.
- [ ] A Hunt remains pending before its deadline and resolves automatically once due without a new chat command.
- [ ] Final Hunt results still award normal Hunt rewards/records and may announce the final outcome in chat without replaying individual rounds.
- [ ] Multiple players can hold independent timed Hunts while Rally/Raid activity remains available.
- [ ] Automatic consumable use remains within the rank cap: C/B 1, A/S 2, S+ 3.
- [ ] Adventure Board shows the active Hunt countdown, duration, progress, and autonomous-use explanation.
- [ ] Portal, Streamer Dashboard, and Player Guide remain readable on desktop and mobile without clipped/overflowing card text.

## Wayfarer Solo Venture

- [ ] Adventure Board shows 80 / 20 Encounter / Treasure and a 3-stage maximum.
- [ ] Encounter shows Attack / Ability / Use Item / Defend and Enemy intent.
- [ ] One click resolves exactly one round; waiting/refreshing does not advance combat.
- [ ] Current HP/MP/AP and consumed items persist when pressing deeper.
- [ ] Stage I/II clear offers Return to Guild and Press On.
- [ ] Stage III banks automatically.
- [ ] Defeat keeps secured XP/JP, recovers half pending Gil, and loses loose item spoils.
- [ ] An active Solo Venture does not occupy the shared Rally/Hunt battle slot.
- [ ] Profile tabs begin Overview → Adventure Board → Jobs → Equipment & Inventory.

## Arsenal Hotfix 6 — Adventure recovery

- [ ] Start or seed a Solo Venture, then run `!clearadventures`; the Solo Venture row is removed and Portal returns to no active Solo Venture after sync.
- [ ] With a timed Hunt active, `!clearadventures` cancels the assignment without granting Hunt rewards.
- [ ] With a field/Rally encounter active, `!clearadventures` clears that encounter.
- [ ] With a Dungeon delve active, `!clearadventures` removes the active run without changing completed Dungeon records or rewards already banked.
- [ ] An active raid/world boss is not cleared.
- [ ] Player progression, inventory, persisted HP/MP/AP, and cooldowns remain unchanged.
- [ ] `!resettimers` remains the separate command for intentionally clearing cooldowns.
