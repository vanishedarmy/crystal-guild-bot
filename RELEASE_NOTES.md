# Crystal Guild v1.7.0 — Production Final

v1.7.0 promotes the completed Retainer Service and Moogle Emporium Annex work to the production release line and freezes the feature set after the final hardening, mobile/UI, item-copy, and hosted performance passes.

## Included feature work

- Retainer Service with timed material procurement, rank/EXP progression, priority procurement, recent-haul history, and final Retainer artwork.
- Moogle Emporium Annex as a shared Fellowship construction unlock, expanding each personal Emporium rotation from 9 to 12 stock slots.
- Gold Saucer v1.6.0 production content carried forward unchanged.
- Restorative-item values verified and locked; item-use copy kept concise.
- Render startup-backup hardening so low disk space cannot trap the Bot in a restart loop.
- Final responsive-layout, compactness, mobile-overflow, and text-spacing cleanup.
- Hosted Web static-art streaming, ETag revalidation, and lazy loading for heavy optional modules.

## Release contract

- Bot runtime: `1.7.0`
- Web runtime: `1.7.0`
- Frontend asset revision: `1.7.0-final`
- Local database schema: **15**
- Hosted sync schema: **1**
- Portal Action protocol: **31**
- Twitch command prefix: `!`

There is no database migration from the final v1.7 Alpha 3/Hotfix baseline. Preserve the existing database, token database, persistent files, and environment secrets when deploying.
