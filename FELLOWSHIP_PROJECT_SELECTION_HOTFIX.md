# Crystal Guild v1.8.2 — Fellowship Project Selection Hotfix

This hotfix keeps the visible release **v1.8.2 — Elite Mercs** and fixes a mismatch between the Fellowship's **Available Guild Work** board and the streamer control used to start that work.

## Fix

The Fellowship page correctly exposed projects such as **Moogle Emporium Annex — Lv. 1** as unlocked, but the owner control still relied on a free-text project query. Human-facing names without the displayed level suffix (for example `Moogle Emporium Annex`) could fail even though the project was genuinely available.

The Streamer Control Center now reads the live `/api/fellowship` project list and presents a **Choose unlocked project…** selector. It submits the authoritative project ID, so anything shown as available can be selected directly.

The Bot resolver is also more forgiving for Twitch/owner text commands. It accepts the full public card name, the facility display name without `Lv.`/`Tier`, and a unique short fragment such as `Annex` or `Archive`. Ambiguous fragments still fail safely.

## Compatibility

- Visible release: `v1.8.2 — Elite Mercs`
- Runtime/frontend: `1.8.2-elite-mercs`
- Local database schema: **18**
- Hosted sync schema: **1**
- Portal Action protocol: **35**
- No migration or player reset.
