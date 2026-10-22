# Crystal Guild v1.9.8 — Twitch Mist Party Support (Venture + Raid)

Bot-only update compatible with **v1.9.8 Airship Expedition**. Version remains
`1.9.8-airship-expedition`. This adds no Web/Portal changes or migrations.

## Commands and effects

| Chat command | Price | Mist HP item | Mist MP item |
|---|---:|---|---|
| `!healparty` / `!healparty 1` | 100 Gil | Potion (50 HP) | Ether (40% max MP) |
| `!healparty 2` | 250 Gil | Hi-Potion (200 HP) | Ether (40% max MP) |
| `!healparty 3` | 500 Gil | Mega-Potion (500 HP) | Hi-Ether (65% max MP) |
| `!healparty 4` | 1,000 Gil | X-Potion (1,000 HP) | Hi-Ether (65% max MP) |

Effects use the current in-game item catalog, but are applied as **party-wide
Mist** support, rather than consuming a physical item from inventory. The
combined price covers both the Mist Potion and Mist Ether effects.

## Gameplay rules

- Stream must be LIVE. The hero must be a participant in the active **Twitch
  Rally Venture** or **Raid**, and combat must have started (not the join rally).
- **One paid party Mist use per player per Venture, and one per player per Raid**.
  Each separate new run resets that type's allowance; other party members may
  sponsor their own once-per-run heals. Selecting a different tier cannot
  bypass the limit.
- Instant recovery affects every **living** member of that same party, capped
  at their max HP/MP. Does **not** revive KO'd heroes, restore AP, or replace the
  sponsor's queued round action. KO'd players cannot sponsor a Mist use.
- If already used, not part of the active party, no combat is active, the
  player lacks Gil, or the party is already at full HP/MP, **no charge and no
  allowance spent**. Insufficient-Gil messages report the exact shortfall.
- Gil debits are recorded as `venture_party_heal` or `raid_party_heal` economy
  transactions. The debit and the roster's per-run receipt commit atomically
  through the shared SQLite runtime checkpoint; retries after restart or across
  concurrent Bot instances cannot charge the same player's use twice.
- Raid healing contributes to the sponsor's tracked raid `healing` total.

## Install

Back up Bot source, database, secrets and runtime state before deployment.

**Patch:** extract
`CrystalGuild_v1.9.8_Stream_Venture_Raid_Mist_Support_Bot_Patch.zip`
into the directory **containing `Bot/`**, merging and replacing its source
files. Designed for v1.9.8 Airship Expedition with or without the previous
Venture-only Mist add-on; it includes both Venture and Raid support.

**Full Bot:** alternatively extract
`CrystalGuild_v1.9.8_Stream_Venture_Raid_Mist_Support_FullBot.zip`
into an **empty staging folder** to obtain one complete, sanitized `Bot/`
source tree including Quick Gear, Airship Expeditions, and both Mist modes.
Do not apply the patch over this full Bot.

Keep the deployed Bot's `.env` and authentication credentials, SQLite database,
overlay/runtime state, and associated Web assets intact. Restart the Bot. This
update requires **no Web rebuild or database migration**.

## Verification

- Focused tests validate exact tier healing, costs and Gil ledger for Venture
  and Raid; independent per-run allowances; rally/nonmember/KO rejections;
  insufficent Gil; rollback; and restart/multi-connection replay safety.
- Python syntax and archive CRC integrity checked. No real Twitch or hosted
  deployment end-to-end test performed; stage with representative accounts.

### Copy/paste Twitch chat announcement

`MIST PARTY HEALS! During a live Venture OR Raid battle, use !healparty (100 Gil), !healparty 2 (250), !healparty 3 (500), or !healparty 4 (1,000) for instant party HP + MP recovery! Once per player per Venture or Raid. No Portal needed!`
