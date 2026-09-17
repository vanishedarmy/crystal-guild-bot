# Crystal Guild v1.8.0 Final — Merc Service Finalization Audit

**Decision: PASS.** v1.8.0 Final promotes the sealed RC3 candidate without feature expansion.

## Release contract

- Runtime/frontend: `1.8.0-merc-final`
- Frontend package: `1.8.0`
- Local database schema: **17**
- Hosted sync schema: **1**
- Portal Action protocol: **34**
- No player reset or Final-specific migration.

## Validation seal

- Frontend: **656/656 PASS**
- Hosted Web/API: **78/78 PASS**
- Bot: **733/733 PASS**
- Python compileall: **PASS**
- JSON integrity: **31/31 PASS**
- Direct static media references: **159/159 present; 0 broken**

## Scope guard

Merc Service pricing, Hunt Seal economy, Hero abilities, three-slot assignment behavior, deployed-state lifecycle/recovery, artwork, and RC3 Portal UI/refresh behavior are unchanged. Final changes release identity, production-facing documentation, validation seal, and packaging only.
