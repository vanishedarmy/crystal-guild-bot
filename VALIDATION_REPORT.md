# Crystal Guild v1.8.2 — Elite Mercs Validation

## Result

**PASS** — the v1.8.2 source trees are ready for release packaging.

## Automated validation

| Check | Result |
| --- | --- |
| Bot unit/regression tests | 748 / 748 passed |
| Hosted Web/API tests | 78 / 78 passed |
| Frontend unit/regression tests | 685 / 685 passed |
| Python compileall | Passed |
| JSON parse validation | 33 / 33 passed |
| Elite Merc artwork set | 18 / 18 passed |
| Elite artwork dimensions | 660 × 880 for all 18 cards |
| Elite artwork optimization | All 18 cards under 400 KB |

## Release-contract validation

- Runtime/frontend identity: `1.8.2-elite-mercs`
- Visible release: `v1.8.2 — Elite Mercs`
- Local database schema: 18
- Hosted sync schema: 1
- Portal Action protocol: 35
- No v1.8.1 → v1.8.2 schema migration is required.
- Existing recruitment records and active Merc contracts remain compatible.

## Elite artwork-state validation

The new `a3` card set contains six Heroes and exactly three cards per Hero:

- `*-locked.webp` — not recruited, silhouette, card status **Locked**.
- `*-unavailable.webp` — recruited and already hired/deployed, card status **Unavailable**.
- `*-available.webp` — recruited and not hired, card status **Available**.

Heroes covered: Lightning, Sephiroth, Rikku, Y’shtola, Noctis, and Cid.

## Packaging note

Crystal Guild Web is distributed as the source project, as in the preceding release packages. Unit/regression validation completed against that source tree. A local `vite build` was not used because the validation environment does not have the npm/Vite dependencies installed; deployment installs the pinned dependencies from `frontend/package.json`.
