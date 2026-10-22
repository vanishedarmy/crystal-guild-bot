# CURRENT RELEASE: v1.9.8 — Airship Expedition

## Twitch Mist Party Healing (Ventures & Raids)

During a live-stream Rally Venture or Raid **combat** phase, participating players may
use `!healparty` (100 Gil), `!healparty 2` (250 Gil), `!healparty 3` (500 Gil), or
`!healparty 4` (1,000 Gil) to immediately heal the entire **living** party's
HP and MP. Mist support can be purchased **once per player per Venture** and
**once per player per Raid**, with separate allowances for each new run.
No physical consumable is needed. Failed uses never deduct Gil. Full rules are
in `HEALPARTY_STREAM_VENTURE_RAID_ADDON.md`.


See `RELEASE_NOTES.md` and the `AIRSHIP_EXPEDITION_198.md` release guide. Existing setup and Queen’s Blood instructions remain relevant to previously released features.

# Current release: v1.9.7 — Queen’s Blood

See `README_FIRST.txt` for this complete release and upgrade instructions. The setup and historical feature documentation below remains available.

# Crystal Guild — Bot (v1.9.7: Queen’s Blood)

The authoritative Twitch/chat engine and player database. Deploy with the matching **v1.9.7** hosted Web service.

- Release: `1.9.7-queens-blood`
- Local SQLite schema: 27; hosted sync schema: 1; Portal Action protocol: 39.
- Standalone Card Hall supports Triple Triad (45 cards, ten opponents and five circuits); the hosted Web service also provides Queen’s Blood.
- Previous v1.9.6 release details are retained in the changelog and historical release notes.

Read `RELEASE_NOTES.md` and `README_FIRST.txt` for complete installation and cleanup. Preserve live data and configured secrets. `FULL_SETUP_README.md`, `RENDER_CLOUD_SETUP.md` and `WEB_SYNC_SETUP.md` remain available for hosting guidance. Historical documents describe their named releases.

## Fast equipment via Twitch chat

After `!recruit` and `!job <starter-job>`, run `!buyweapon`, `!buyarmor`, or `!buyaccessory`. The command selects the highest appropriate tier currently in your personal Moogle Emporium rotation, favoring relevant bonuses for your active Job. It purchases and equips the item in one atomic action, honors regional stock/Job/level restrictions and Guild discounts, and reports the remaining Gil. If the best item costs more Gil than you have, it reports the price, balance, and shortfall without spending anything or substituting lower gear. Already owned? It equips for free. If better gear is equipped, it stays equipped. No Portal visit is required.
