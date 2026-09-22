# Crystal Guild v1.9.0 Alpha 7 — Hall of Trophies Validation

Validation target: runtime/frontend `1.9.0-hall-of-trophies-alpha7`, local schema **20**, hosted sync schema **1**, Portal Action protocol **36**.

## Automated results
- Bot full regression suite: **792 / 792 passed**.
- Focused Hall of Trophies Bot suite: **4 / 4 passed**.
- Hosted Web/backend Python suite: **80 / 80 passed**.
- Frontend Node history suite: **691 / 752 passed**.
- Exact Hotfix 10 baseline in this package environment: **689 / 750 passed** with the same **61 inherited historical release-identity / legacy asset-policy failures**.
- Alpha 7 adds two passing frontend tests and introduces **zero new frontend failure names** relative to the exact Hotfix 10 archive.
- Python source compilation: **passed** for Bot and Web packages.

## Hall coverage
- 30 unique trophy IDs with sealed category split: **11 World Events / 5 Raids / 4 Hunts / 4 Triple Triad / 6 Fellowship**.
- Schema-20 ownership and exact World Event clear history are idempotent and foreign-key backed.
- World Event trophies require exact variant history; the system does not infer old variants from generic encounter data.
- Raid/Hunt/Triple Triad reconciliation uses authoritative per-player records.
- Fellowship construction trophies require the exact project contributor record plus completed facility tier.
- Derived category trophies self-repair from their constituent accomplishments.
- In-process Portal synchronization reconciles progress before producing the profile snapshot.

## Packaging/artwork
- **30** individual Trophy WebP files plus **4** Hall support assets are packaged under `/trophies/a1/`.
- Static catalog/art remains in the Web build; hosted player snapshots transmit compact Trophy ownership only.
- Hall UI covers filters, sorting, NEW presentation, details, completion progress, focus restoration, reduced-motion handling, and narrow-mobile containment.

## Frontend build environment
The source package does not include installed `node_modules`, so a production Vite bundle was not rebuilt inside this isolated workspace. Source-contract/history tests execute directly and the new Hall checks pass. Normal deployment should install the pinned frontend dependencies before running the production build.
