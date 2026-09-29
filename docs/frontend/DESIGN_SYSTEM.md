# Design System

**Status:** authoritative for `apps/web`. The components in `src/components/` cite this
document by section; a rule that is not written here is not a rule.

## 1. Tokens

All colour, radius and spacing values are CSS custom properties in
`src/app/globals.css`. A component never writes a raw hex value, because a raw
value cannot be re-themed and cannot be checked against both colour schemes.

| Token | Purpose |
|---|---|
| `--ink` · `--ink-soft` · `--ink-faint` | three steps of text emphasis |
| `--surface` · `--surface-2` | page and raised backgrounds |
| `--line` | every border |
| `--color-forest` | the single action colour |
| `--radius-8` | the control radius |
| `--ink-muted` | decorative only, never text |

**Contrast is a token property, not a component property.** A 2026-09-26 axe scan of
the `ar` and `ur` routes measured the `.chip` label at 4.18:1 against `--surface-2`,
below the 4.5:1 that 11px text requires, so `.chip` uses `--ink` rather than
`--ink-soft`. When a token is used for small text, verify it at that size; 3:1 is
the large-text allowance and does not apply below 18px.

## 2. The `chip` component

A `chip` is a compact, non-interactive label that names a fact and, where the fact
has a source, the source.

- **Source first.** A chip that states a figure carries the value's provenance.
  `ProvenanceStamp` renders `<span data-provenance="<path>">` so a test can read the
  source back out of the DOM.
- **Verified only when the payload says so.** A 200 response proves the gateway
  answered, not that the value was measured. `verificationOf` in `lib/api/surfaces`
  reads the claim from the payload; a route that asserts nothing renders unverified
  with an explicit note.
- **`label ?? children`.** A call site that passes both a `label` and an `<h1>` child
  renders the label and **silently drops the heading**. Sixty-one pages were in that
  state. Pass a heading beside the stamp, not inside it. A unit test scans every
  source file for the pattern.
- **Never interactive.** A chip is not a button, a link, or a tab. If it needs to be
  pressable it is a different component.

## 3. Page shell

Every route renders, in this order:

1. a skip link targeting `#main-content`
2. a single `<main id="main">`
3. exactly one `<h1>`

Nested or duplicated `main` elements are invalid, and two `<h1>` elements make the
document outline ambiguous. `FivePart` takes a `headingLevel` prop for exactly this
reason: it defaults to `1` and a page that already renders a title passes `2`.

## 4. Data surfaces

A page bound to a gateway route shows the payload and names the path it read.

- **The exact path appears on the page.** A reader must be able to ask the gateway
  the same question.
- **The column set comes from the response.** Most routes publish an empty or
  `additionalProperties: true` schema, so a declared table shape would be a guess.
  `RecordTable` and `ShapeView` read the columns back from the payload; the header
  row is the dataset's own field names.
- **A missing value renders an em dash.** Never a zero, never a blank that reads as
  a measurement.
- **Every surface renders the same states:** ready, empty, error, offline,
  unauthorized, unavailable. `toDataState` is the single mapping from an
  `ApiResult` to one of them.

## 5. Direction and locale

Layout uses logical properties only — `ms`, `me`, `ps`, `pe`, `text-start`,
`text-end` — and never assumes left-to-right geometry. `fa`, `ar` and `ur` are RTL;
the document direction is set by the locale layout and covered by `tests/rtl.spec.ts`
for all three.

Error boundaries are the one place the message provider is unavailable:
`app/global-error.tsx` replaces the root layout, and a boundary above the locale
segment has no provider either. They read from `lib/error-copy`, which resolves the
locale from the URL. Visible text is not hard-coded in a component.

## 6. Interactive controls

- A control is a `<button>` or an `<a>`; a `<div>` with a click handler is not.
- Every input has a label, and an icon-only control carries an accessible name.
- Focus is visible on every focusable element, and focus order follows the DOM.
- Motion respects `prefers-reduced-motion`.
- A form that works without JavaScript uses a plain `GET` form. The content search
  and the site reference are built this way deliberately.

## 7. What this document does not cover

Content, copy and language choice. The catalogs in `apps/web/messages/` are the
authority for text, and `scripts/check-message-usage.mjs` and
`scripts/check-locale-depth.mjs` hold them to it.
