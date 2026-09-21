# Simple Render Setup — v1.9.0 Alpha 4 Navigation Accessibility

1. Preserve the existing Render persistent disk and secrets.
2. Deploy the matching v1.9.0 Alpha 1 Bot and Web packages together.
3. Restart the Bot; it creates a verified `pre_schema_19_*.db` backup and migrates schema 18 → 19 automatically.
4. Confirm runtime `1.9.0-navigation-accessibility-alpha4`, schema **19**, hosted sync **1**, and Portal protocol **36**.
5. Verify the Moogle Trading Post appears in Fellowship services and the Moogle Emporium once constructed.
6. Confirm listing, purchase, cancellation, expiry return, and seller payout behavior before reopening live commerce.
