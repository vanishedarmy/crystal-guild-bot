# Hunt Board Hotfix 1 — Bot Upgrade Guide

1. Back up the existing Crystal Guild database.
2. Stop the current Bot worker.
3. Apply the Bot package or patch over the current v1.1.17 Arsenal II Hotfix 5 / runtime `1.1.17-arsenal-ii-h4` installation.
4. Preserve `.env`, Twitch tokens, database files, and other runtime secrets/state.
5. Start the Bot and verify `!cgversion` reports `1.1.18-hunt-board-h1`.
6. Check `!hunts` and confirm the timer line reads C 15m · B 30m · A 2h · S 5h.
7. Dispatch a Hunt and confirm no chat combat is requested and the expected return matches its rank timer.

No schema migration, OAuth reconfiguration, Portal Action protocol change, or player reset is required.
