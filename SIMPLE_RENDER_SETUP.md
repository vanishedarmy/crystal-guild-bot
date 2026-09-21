# Simple Render Setup — v1.9.0 Alpha 6 World Events

1. Preserve the existing Render persistent disk and secrets.
2. Deploy the matching v1.9.0 Alpha 6 Bot and Web packages together.
3. Restart the Bot. Existing schema 19 databases open in place; older schema 18 databases still use the verified `pre_schema_19_*.db` migration backup path.
4. Confirm runtime `1.9.0-world-events-alpha6`, schema **19**, hosted sync **1**, and Portal protocol **36**.
5. Verify the Moogle Trading Post appears in Fellowship services and the Moogle Emporium once constructed.
6. Confirm listing, purchase, cancellation, expiry return, and seller payout behavior before reopening live commerce.
