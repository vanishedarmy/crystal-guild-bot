# Crystal Guild v1.8.0 RC3 — Validation Report

RC3 validates the navigation/readability and refresh-control polish pass against the sealed RC2 package.

## Completed validation

- Frontend Node regression suite: **656/656 PASS**.
- Hosted Web/API Python suite: **78/78 PASS**.
- Bot Python suite: **733/733 PASS**.
- Python compileall: **PASS** for Bot and hosted Web modules.
- Static media-reference audit: **161 unique references checked: 160 static files present, 1 expected dynamic region template; 0 broken static references**.
- No gameplay, Hunt Seal economy, schema, sync, or Portal protocol changes.

## UI polish coverage

- Standard desktop navigation uses six readable columns with a centered four-item final row.
- Very wide desktop uses eight columns; compact desktop/tablet uses four and two columns before the mobile selector takes over.
- Profile navigation labels remain single-line and are contained within their button geometry.
- No feature panel exposes a section-specific manual Refresh button.
- One shared Refresh control appears at the bottom of live Portal pages.
- Automatic live updates and post-action refresh behavior remain active.
- The connection status strip is passive and no longer creates or polls PING actions from the UI.

## Release contract

- Runtime/frontend: `1.8.0-merc-rc3`
- Local database schema: **17**
- Hosted sync schema: **1**
- Portal Action protocol: **34**
- No player reset or migration.
