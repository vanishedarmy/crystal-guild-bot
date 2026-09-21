# Crystal Guild v1.9.0 Alpha 5 — Title Status Hardening Finalization Audit

## Release identity
- Visible release: **v1.9.0 Alpha 5 — Title Status Hardening**
- Runtime/frontend: `1.9.0-title-status-hardening-alpha5`
- Frontend package: `1.9.0-alpha.5`
- Local schema: **19**
- Hosted sync: **1**
- Portal Action protocol: **36**

## Scope verified
- Existing heroes are reconciled against the current achievement catalog on Bot startup.
- Hosted snapshots reconcile the requested hero before a profile snapshot is built when running in-process sync.
- Existing achievement rows repair missing reward-Title rows without duplication.
- Achievement dependencies resolve to a fixed point instead of depending on catalog order.
- Permanent unlocks remain visually complete even when reversible current values later decrease.
- Portal achievement progress supports the same current requirement families used by the Bot, including Expedition-region progress.
- Secret achievement names, conditions, and progress remain concealed until unlock.
- Alpha 4 Navigation Accessibility remains intact.
- No economy, Gold Saucer payout, Title requirement, schema, or Portal Action changes are introduced.
