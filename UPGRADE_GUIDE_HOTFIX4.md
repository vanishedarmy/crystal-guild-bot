# Bot Upgrade — RC1 Hotfix 4

1. Back up the current Crystal Guild SQLite database and `.env`.
2. Replace the Bot runtime with this package or apply the RC1 -> RC1H4 Bot patch.
3. Keep your existing `.env` and persistent data. No migration is required.
4. Restart the Bot.
5. Test `!camp` while OFFLINE and while LIVE. The base timer should be 1 hour OFFLINE and 15 minutes LIVE before Fellowship reductions.
6. Deploy the paired Web RC1H4 package so the Adventure Board and Player Guide describe the same rule.
