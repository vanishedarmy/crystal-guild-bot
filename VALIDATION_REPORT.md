# v1.9.7 validation

107 Queen’s Blood tests, 33 hosted Portal Action tests, 33 carried-forward Bot regression tests, and five frontend identity/Emporium checks pass. The production frontend builds successfully.

All 48 full-size portraits and 48 display previews decode correctly, match their manifests, and are identical between the source and built static trees. Full-size portraits preserve the approved source pixels; previews retain the whole frame at 320×480.

Sixteen browser checks cover the tutorial, move previews and persistence, collection search, full-art dialogs and focus return, deck saving, six widths from 320 to 1390 pixels, live invitations between two synthetic accounts, automatic opponent updates, offline/reconnect behavior, and correspondence invitations. No browser JavaScript errors were observed.

Fifty-six deterministic games across all 14 opponents finish within the bounded simulation. This verifies termination under that strategy, not human win rates or exhaustive balance.

The historical frontend suite reports 774 passing and 102 failing assertions out of 876. These inherited release/layout/asset expectations are recorded in the complete JSON report; the suite is not claimed to be entirely green. An older Seasonal Events Alpha 8 schema assertion also fails on the approved baseline because it expects schema 26 instead of 27.

Tests use local synthetic accounts and databases. No live deployment, real-user invitations, or real transactions were performed. See `VALIDATION_v1_9_7.json` in the full package for details.
