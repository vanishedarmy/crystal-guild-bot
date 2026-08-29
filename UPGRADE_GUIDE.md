# Upgrade Guide — Crystal Guild v1.3.0 Guild Expansion Alpha 5

Baseline: **v1.3.0 Guild Expansion Alpha 4**.

1. Back up the live Crystal Guild database and persistent Twitch/token data as normal.
2. Stop the Bot cleanly.
3. Apply the Alpha 4 → Alpha 5 Bot patch, or replace application files with the full Alpha 5 Bot package while preserving `.env`, database files, token storage, and persistent-disk paths.
4. Apply the matching Alpha 4 → Alpha 5 Web patch/full Web package and redeploy the hosted Web service.
5. Restart the Bot. No schema migration is required; schema **9** remains current.
6. Existing Guild progress is evaluated against the new Legacy accomplishments once. Any accomplishments already earned are granted retroactively and recorded so they cannot pay twice.
7. Confirm `!cgversion` reports `1.3.0-guild-expansion-a5`.
8. Confirm `/api/health` reports runtime/frontend revision `1.3.0-guild-expansion-a5`, hosted sync schema **1**, and Portal Action protocol **21**.
9. Open Fellowship and verify the new **Guild Legacy** section appears. Open your own Fellowship tab and verify the **Guild Service Record**.
10. Test `!legacy` and `!guildrecord` in chat.

No player reset, OAuth change, or new environment variable is required.
