# Crystal Guild v1.7.0 — Retainer Service Alpha 1 Simplified Render Setup

1. Preserve the existing persistent disk/database and environment secrets.
2. Deploy this Bot build.
3. Deploy the matching v1.7.0 Retainer Service Alpha 1 Web build.
4. Confirm `!cgversion` = `1.7.0-retainer-a1`, schema = **14**, Portal protocol = **30**, and `!health` is clean.
5. Open Retainer Service in the Adventurer Portal and perform a state check/dispatch smoke test.

Alpha 1 requires no new environment variable and does not reset player progression.
