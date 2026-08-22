# Crystal Guild v1.1.14 — Cloud Continuity Manual Checklist

- [ ] `!cgversion` reports `1.1.14-cloud-continuity`.
- [ ] `!health` reports DB, combat, notifications, Portal Actions and in-process sync healthy.
- [ ] Existing player progression is intact.
- [ ] Redeploy/restart Web and confirm Fellowship repopulates within one heartbeat without restarting Bot.
- [ ] Start/inspect a raid and confirm `/api/overlay/state` updates.
- [ ] OBS Browser Source at `/overlay` renders raid state and hides when no raid is active.
- [ ] Persistent `/var/data` survives Bot deploy.
