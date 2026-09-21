# Crystal Guild v1.9.0 Alpha 4 — Navigation Accessibility

Alpha 4 improves the adventurer profile navigation without changing gameplay balance or player progression. The existing Crystal Guild navy/gold identity remains intact, while each destination gains a restrained accent family for faster visual recognition.

## Navigation changes
- Section buttons now use subtle color families while retaining their icon and text labels, so color is never the only identification cue.
- Active tabs use stronger borders, brighter copy, accent glow, and the existing `aria-selected` state.
- Keyboard focus uses a high-contrast gold outline independent of the section accent.
- Responsive layout is 6 columns on wide desktop, 4 on compact desktop, 3 on tablet, and 2 touch-friendly columns on mobile.
- Mobile keeps the actual navigation buttons instead of replacing them with the generic section dropdown; long labels may wrap safely.
- `prefers-contrast: more` and `prefers-reduced-motion: reduce` receive explicit treatments.

## Carried forward unchanged
- v1.9.0 Alpha 3 Title Expansion and retroactive achievement/title evaluation.
- v1.9.0 Alpha 2 economy balance and Gold Saucer payouts.
- Moogle Trading Post, Merc Service, Fellowship, Resynthesis, Retainers, inventory/equipment, and all existing progression.

## Compatibility
- Runtime/frontend: `1.9.0-navigation-accessibility-alpha4`
- Local schema: **19**
- Hosted sync schema: **1**
- Portal Action protocol: **36**
- No database migration or player reset is required.
