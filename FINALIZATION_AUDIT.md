# Finalization Audit — Crystal Guild v1.7.1 Resynthesis Alpha 2 Hotfix 3

**Decision: PASS — Job Resource Persistence.**

Hotfix 3 fixes MP/AP state loss across Job-family switches by removing both inactive-resource clobber paths: full player refreshes and equipment normalization now update only the resource family used by the active Job. A one-time runtime-receipt compatibility repair handles inactive zeros already written by older builds without creating a repeatable Job-swap refill mechanic.

Verification covers preserved inactive values, one-time legacy repair, legitimate zero persistence, full Bot regression, unchanged Web/API compatibility, source parsing, JS/CSS syntax, and artwork decode.

Validation: **686/686 Bot**, **562/562 frontend**, **65/65 hosted Web/API**, **121/121 Bot Python**, **16/16 Web Python**, **205/205 JS/MJS**, **8/8 CSS**, **843/843 WebP**, **0 public PNG**.

Bot runtime `1.7.1-resynthesis-a2h3`; paired Web `1.7.1-resynthesis-a2`; schema **15**; hosted sync **1**; Portal protocol **32**; prefix `!`. No migration or player reset. Job Quest Hotfix 2, Encounter Variety Hotfix 1, Resynthesis, and the Alpha 2 Gold Saucer rebalance are carried forward unchanged.
