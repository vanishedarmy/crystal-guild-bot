# Crystal Guild v1.7.0 — Moogle Emporium Annex Alpha 3 Simplified Render Setup

1. Preserve the existing persistent disk/database and environment secrets.
2. Deploy this Bot build.
3. Deploy the matching v1.7.0 Moogle Emporium Annex Alpha 3 Web build.
4. Confirm `!cgversion` = `1.7.0-emporium-annex-a3h1`, schema = **15**, Portal protocol = **31**, and `!health` is clean.
5. Open Retainer Service in the Adventurer Portal and perform a state check/dispatch smoke test.

Alpha 2 requires no new environment variable and does not reset player progression.
