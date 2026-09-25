# Internationalization and RTL

**Decision:** Adopt the catalog and layout rules in [`../adr/0001-language-strategy.md`](../adr/0001-language-strategy.md) and the accessibility gate in the Decision Freeze.

## Locale contract

The official locale set is:

`en`, `fa`, `ar`, `ur`, `de`, `es`, `fr`, `hi`, `it`, `ms`, `pt`, `ru`, `zh`, `bn`

- `messages/en.json` is the canonical catalog.
- Every route has a required locale prefix.
- The normal fallback is requested locale to `en` only. A transitional `fa` fallback must be explicit, measured, and removed after parity is complete.
- Every new key exists in all 14 catalogs. CI must reject missing or extra keys.
- Visible product text is not hard-coded in components.

## Formatting

- Use ICU `MessageFormat` for plural and select messages, including the `other` branch.
- Use `Intl.NumberFormat`, `Intl.DateTimeFormat`, and `Intl.RelativeTimeFormat` with the active locale and the correct time zone.
- Keep units, dates, and scientific values in an explicit locale rather than concatenating translated fragments.
- Machine-translated entries carry a quality marker and are reviewed before release.

## RTL and layout

`fa`, `ar`, and `ur` are RTL. Layout must use logical CSS properties (`ms`, `me`, `ps`, `pe`, `start`, `end`, `text-start`, and `text-end`) rather than assuming left-to-right geometry. Keep focus order, skip links, and keyboard behavior independent of direction. Isolate numbers, identifiers, and URLs with `dir="ltr"` or an appropriate `bdi` element.

## Verification gate

- Catalog parity for all 14 locales.
- Production build and route tests for representative LTR and RTL locales (`en`, `fa`, `ar`, and `ur`).
- Reflow at 320×256, zoom at 200%, keyboard-only navigation, visible focus, and reduced-motion checks.
- Zero axe violations for the agreed WCAG 2.2 AA tags; a critical-only filter is not sufficient.
- Visual and copy checks for truncation, mixed-direction numbers, dates, and error messages.

A locale is not complete when its JSON file exists; it is complete only when the key, formatting, direction, accessibility, and CI checks pass together.
