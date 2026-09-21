# Crystal Guild v1.9.0 Alpha 3 — Title Expansion Validation

Validation target: runtime `1.9.0-title-expansion-alpha3`, local schema **19**, hosted sync schema **1**, and Portal Action protocol **36**.

## Automated results
- Bot full regression suite: **766 / 766 passed**.
- New Alpha 3 title-expansion Bot tests: **7 / 7 passed**.
- Hosted/Web Python suite: **80 / 80 reported OK**. In this isolated container the hosted-server test process can retain test threads after unittest prints its successful summary, so the outer command may need to be bounded after completion.
- Focused frontend Title Expansion + Economy Balance regressions: **7 / 7 passed**.
- Full frontend history suite: **646 / 703 passed**. The remaining **57** failures are the exact same inherited historical assertions present in the Alpha 2 baseline (**642 / 699**, also 57 failures); Alpha 3 added four passing tests and introduced **zero new full-suite failure names**. These historical failures include old releases asserting that their version label is still current and legacy PNG-policy assertions.
- Python compile checks: Bot and Web passed.
- GameData validation: **0 errors**.
- Title reference audit: **121 titles**, **89 achievements**, zero missing achievement reward-title references, zero missing Gold Saucer prize-title references.

## Functional Alpha 3 coverage
- New Prize Counter title prices are enforced at 750 / 1,000 / 1,250 / 1,500 MGP.
- Gold Saucer Challenge Titles are exposed separately from purchasable prizes.
- Lifetime MGP, jackpot, Monster Toss, Chocobo Racing, Triple Triad, attraction-variety, and participation metrics use persistent authoritative records.
- **Golden Saucer** unlocks after six other Gold Saucer achievements.
- Secret challenges hide name, reward, condition/progress presentation, and title identity until completion.
- **Oh hi Mark.** remains hidden until the same Hunt mark has been cleared three times.
- Portal achievement snapshots support all new requirement types.

## Compatibility
No schema or Portal protocol changes are required from v1.9.0 Alpha 2. Existing economy balance and Trading Post behavior are retained.
