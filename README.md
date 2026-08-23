# Crystal Guild v1.1.15 — Wayfarer Hotfix 3

Wayfarer adds persistent player-paced Solo Ventures and schema-5 Solo Venture state. Hotfix 3 adds the authoritative Bot-side `SET_TITLE` Portal action so earned Titles can be equipped from the Adventurer Portal as well as Twitch chat.

Runtime `1.1.15-wayfarer-h3` · local DB schema **5** · hosted sync schema **1** · hosted sync compatibility `1.1.15-wayfarer` · Portal Action protocol **14** · Twitch prefix `!`.

Hotfix 3 does not change the database schema and requires no player reset, new Render secret, or new Twitch OAuth scope. Deploy the matching Web build (`1.1.15-wayfarer1h3`) because Bot and Web must agree on Portal Action protocol 14.

See `UPGRADE_GUIDE.md`, `RELEASE_NOTES.md`, and `FULL_SETUP_README.md`.
