# Upgrade to v1.7.1 Resynthesis Alpha 2 Hotfix 1

This is a **Bot-only encounter-selection hotfix**. Deploy the Hotfix 1 Bot over the existing v1.7.1 Resynthesis Alpha 2 Bot. The Alpha 2 Web build remains compatible and does not need to change.

Preserve the live database, token database, persistent storage, and all secrets. No database migration is required: schema remains **15**, hosted sync remains **1**, and Portal Action protocol remains **32**. Existing progression, MGP, Gold Saucer history, Resynthesis state, Retainers, inventory, and active content are preserved.

After restart, confirm `!cgversion` reports Bot runtime `1.7.1-resynthesis-a2h1`, then run several Ventures/Solo Ventures in a familiar region and confirm encounter variety is restored.
