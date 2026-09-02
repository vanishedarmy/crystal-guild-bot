# Upgrade to Crystal Guild v1.7.0 Moogle Retainer

1. Back up the live deployment and preserve the existing database, Twitch token database, persistent files, and environment secrets.
2. Deploy the v1.7.0 Moogle Retainer Bot and Web together.
3. Do **not** replace the live database with any packaged/example database.
4. No database migration or schema migration is required from the immediately prior schema-15 v1.7.0 candidate baseline; schema remains **15**.
5. Confirm the Bot reports runtime `1.7.0`, schema **15**, and Portal protocol **31**.
6. Confirm the Web reports runtime `1.7.0` and frontend asset revision `1.7.0-final`.
7. Verify Retainer dispatch/collection, Moogle Emporium Annex stock capacity, Portal sign-in, and one normal startup/restart cycle.

Render deployments should leave database storage on the persistent disk. Routine file logs remain on temporary storage, and startup backup pruning runs before a new backup copy is attempted.
