# Crystal Guild v1.7.0 — Moogle Emporium Annex Alpha 3

Alpha 3 adds the **Moogle Emporium Annex**, a small one-time Fellowship construction project that permanently expands the personal Emporium for the whole Guild.

The Annex unlocks at **Fellowship LVL 3** and requires **20,000 Gil**, **12 Mythril Ore**, and **20 crafted items** alongside the level requirement. When construction completes, every recruited adventurer's personalized Moogle Emporium rotation expands from **9 to 12 stock slots**.

The original nine-slot shop composition remains the foundation of each rotation; the Annex adds three further weighted picks from the same level/job-eligible merchandise pool without duplicates. Prices, sell values, refresh timing, item definitions, and purchase rules do not change. Because there are three additional picks, players have more choice per rotation, which is the intended Annex benefit, but nothing is granted for free.

Existing nine-slot cached shop rotations detect the new Guild capacity and rebuild automatically after Annex completion, so the benefit is visible immediately on the next shop request rather than waiting for the prior rotation timer.

The Fellowship public Guild Board now displays the Annex as a sixth facility card while the existing five-major-facility Legacy accomplishments remain unchanged. The Portal's Fellowship Services and Moogle Emporium panels both show Annex status and current stock capacity.

Runtime advances to `1.7.0-emporium-annex-a3`. Local database schema remains **15**, hosted sync remains **1**, Portal Action protocol remains **31**, and the Twitch command prefix remains `!`. Retainer Service Alpha 2, Gold Saucer v1.6.0, and all existing progression carry forward unchanged.
