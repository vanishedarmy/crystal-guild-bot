# Crystal Guild v1.7.0 — Moogle Emporium Annex Alpha 3 — Item Usage Copy Hotfix 2

Hotfix 2 trims the recovery-item copy introduced in Hotfix 1.

Recover & Equip now shows only each item's declared effect, such as **Restores 50 HP**, **Restores 500 HP**, **Restores 65% max MP**, or **Revives with 30% HP**. The extra “Effective now,” potency, cap, and overheal explanation text has been removed.

Field-use results are also shorter. After an item is used, the result reports the amount or resource actually restored without the previous potency/cap explanation or trailing HP/MP/AP snapshot.

No restorative values changed. Potion remains **50 HP**, Hi-Potion **200 HP**, Mega-Potion **500 HP**, and X-Potion **1,000 HP**. The existing MP/AP percentage restoratives, Phoenix Down, Tent, Elixir, and Megalixir behavior are unchanged.

Runtime/frontend revision: `1.7.0-emporium-annex-a3h2`. Local database schema remains **15**, hosted sync remains **1**, Portal Action protocol remains **31**, and Twitch prefix remains `!`. No migration, item rebalance, inventory rewrite, artwork change, or Annex change is required.
