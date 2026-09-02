# Crystal Guild v1.7.0 — Moogle Emporium Annex Alpha 3 — Item Recovery Integrity Hotfix 1

This hotfix audits and locks the restorative item contract without changing item balance.

The underlying recovery values were confirmed correct: **Potion 50 HP**, **Hi-Potion 200 HP**, **Mega-Potion 500 HP**, and **X-Potion 1,000 HP**. Ether tiers restore **40% / 65% / 100% maximum MP**; Stamina Draught / Warrior’s Tonic / Hero’s Brew restore **40% / 65% / 100% maximum AP**; Phoenix Down revives at **30% maximum HP**; Tent and Elixir fully restore the applicable personal resources; Megalixir fully restores living party members in Active Battle.

The apparent Mega-Potion discrepancy in Recover & Equip was an **overheal presentation issue**, not a potency bug. Recovery always stops at the target’s maximum resource. A hero missing 59 HP therefore receives 59 HP from a 500-HP Mega-Potion, with the remaining 441 unable to exceed maximum HP.

Hotfix 1 makes that distinction explicit. Recover & Equip now displays both the item’s declared potency and its current effective recovery (for example, **Restores 500 HP · Effective now +59 HP**). Field-use result text also identifies when recovery was capped at the target’s maximum resource.

Regression coverage now locks the fixed Potion ladder, fractional MP/AP restoratives, Portal effective-recovery previews, and capped-use messaging. Shared battle item resolution continues to cover Active Battle, Solo Venture, Expedition, Dungeon and timed Hunt combat; raid item resolution was separately audited.

Runtime/frontend revision: `1.7.0-emporium-annex-a3h1`. Local database schema remains **15**, hosted sync remains **1**, Portal Action protocol remains **31**, and Twitch prefix remains `!`. No database migration, inventory rewrite, item-value rebalance, or artwork change is required.
