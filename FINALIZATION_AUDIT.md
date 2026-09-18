# Crystal Guild v1.8.1 — Merc Recruitment Finalization Audit

**Decision: PASS.** v1.8.1 adds permanent Merc recruitment and the Dungeon Portal revision repair on top of the v1.8.0 Merc Service release line.

## Release contract

- Runtime/frontend: `1.8.1-merc-recruitment`
- Frontend package: `1.8.1`
- Local database schema: **18**
- Hosted sync schema: **1**
- Portal Action protocol: **35**
- Verified automatic `pre_schema_18` migration backup.
- No player reset.

## Validation seal

- Frontend: **670/670 PASS**
- Hosted Web/API: **78/78 PASS**
- Bot: **738/738 PASS**
- Python compileall: **PASS**
- JSON integrity: **PASS**
- Expansion Merc card artwork: **18/18 present** and web optimized.

## Scope guard

The founding six Merc Heroes and established Hunt Seal deployment economy remain intact. v1.8.1 adds six permanently recruitable expansion Heroes, recruitment/registry presentation, their three-state artwork families, protocol support for `MERC_RECRUIT`, and revision-preserving Dungeon Portal mutations.
