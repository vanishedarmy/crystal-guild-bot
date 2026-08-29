# Crystal Guild v1.3.1 — Asset Optimization

## Maintenance Release

v1.3.1 reduces the shipped Crystal Guild footprint without changing gameplay, balance, progression, schemas, or Portal behavior.

### Artwork optimization
- Audited all **390** remaining PNG files in the shipped Web public asset tree.
- Converted an asset only when **lossless WebP** was smaller than its PNG source. All 390 qualified.
- PNG artwork total: **144.21 MiB**.
- Replacement WebP total: **112.27 MiB**.
- Raw artwork savings: **31.93 MiB (22.1%)** for the converted set.
- Every conversion preserves dimensions, transparency, and decoded RGBA pixels exactly.
- Existing WebP assets were also audited; they were left unchanged when repacking did not provide a meaningful reduction.

### Runtime/reference cleanup
- All active artwork mappings, manifests, CSS/HTML references, and frontend regression expectations now point to the optimized WebP assets.
- The hosted static server already supports `image/webp`; PNG MIME support remains available for future/third-party assets.
- Corrects two stale current-package version surfaces discovered during the audit: the Web package `__version__` and raid-overlay cache-busting revision.
- Adds release regression coverage that fails if shipped public PNG artwork or stale current runtime identities return.

### Compatibility
- Bot runtime: `1.3.1-asset-optimization`
- Hosted Web runtime: `1.3.1-asset-optimization`
- Frontend asset revision: `1.3.1-asset-optimization`
- Local DB schema: **9** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **22** unchanged
- Twitch prefix: `!`
- Database migration: **none**
- Player reset: **none**
- OAuth changes: **none**
- New environment variables: **none**
- Gameplay/economy changes: **none**
