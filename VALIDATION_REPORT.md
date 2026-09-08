# Validation Report — Crystal Guild v1.7.1 Resynthesis Alpha 2 Hotfix 5 — Treasure Seekers Solo Progress

**PASS**

- Bot runtime/frontend contract: `1.7.1-resynthesis-a2h5`
- Local DB schema: **15**; hosted sync: **1**; Portal protocol: **32**
- Bot regression: **689/689 PASS**
- Focused Solo Treasure → Treasure Seekers regression: **PASS**
- Frontend regression (unchanged paired Web): **568/568 PASS**
- Hosted Web/API (unchanged paired Web): **65/65 PASS**
- No database migration or player reset required.

The focused regression confirms that one Solo treasure discovery records exactly one replay-safe `treasure` Fellowship event, advances Treasure Seekers by one when active, and also advances the Treasure Hunters deed by one.
