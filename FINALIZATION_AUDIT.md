# Gold Saucer Alpha 5 Release Audit — Crystal Guild v1.6.0 — Gold Saucer Alpha 5 Hotfix 5 — Triple Triad Full Card Face Sync

Hotfix 5 is a matched Bot + Web release because five authoritative Triple Triad card definitions change to match the printed artwork. No persistent schema or protocol change is needed.

Runtime `1.6.0-gold-saucer-a5h5`; local DB schema **13**; hosted sync **1**; Portal Action protocol **29**; prefix `!`; MGP canonical.

Release gates: **632/632 Bot**, **516/516 frontend**, **56/56 hosted Web/API**, **800/800 WebP decode**. Packaging must exclude live databases, `.env` files, caches, and runtime overlay state.
