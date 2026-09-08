# Upgrade to v1.7.1 Resynthesis Alpha 2 Hotfix 5

This is a **Bot-only Job Resource Persistence repair**. Deploy the Hotfix 3 Bot over v1.7.1 Resynthesis Alpha 2 Hotfix 2. The existing Alpha 2 Web build remains compatible and does not need to change.

Preserve the live `crystal_guild.db`, Twitch token database, persistent storage, and environment secrets. No database migration is required; schema remains **15** and Portal protocol remains **32**.

On the first Hotfix 3 startup, the Bot performs a one-time compatibility repair for inactive MP/AP zeros written by the old refresh/normalization bug. It does not reset active resource pools, player progression, inventory, Jobs, Gold Saucer state, Retainers, or Resynthesis data.

After restart:
1. Confirm `!cgversion` reports `1.7.1-resynthesis-a2h5`.
2. Switch from an MP Job to an AP Job (and vice versa) and confirm the destination resource meter is preserved/initialized rather than being erased by the switch.
3. Switch back and confirm the original resource pool still has its prior value, subject only to the destination Job's normal maximum clamp.
4. Confirm a legitimately depleted `0` resource remains `0` after switching away and back; Job swapping must not refill it.
