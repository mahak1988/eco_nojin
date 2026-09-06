# Eco Nojin Design System

## Typography Scale

| Role | CSS class | Usage |
|------|-----------|-------|
| `display` | `text-display` | Hero page titles |
| `h1` | `text-h1` | Page headings |
| `h2` | `text-h2` | Section headings |
| `h3` | `text-h3` | Card titles |
| `h4` | `text-h4` | Inline labels |
| `bodyLg` | `text-bodyLg` | Lead paragraphs |
| `body` | `text-body` | Body text |
| `bodySm` | `text-bodySm` | Secondary text |
| `caption` | `text-caption` | Captions, metadata |
| `overline` | `text-overline` | Overlines, badges |

Weights: `font-thin` … `font-black` via `fontWeight` map.

## Semantic Color Tokens

```ts
semanticTokens: {
  soil, water, carbon, vegetation, climate, satellite,
  success, warning, danger, info, neutral
}
```

Helpers: `tokenToBgClass(token)`, `tokenToTextClass(token)`.

## Spacing Scale

`numericSpacing` (0–96) maps to Tailwind `spacing` scale. `semanticSpacing` aliases: `componentXS` … `pageLG`.

## Dark Mode Contract

- Toggle via `ThemeToggle` component (sets `class="dark"` on `<html>`).
- Persisted in `localStorage` under key `eco.theme`.
- Falls back to `prefers-color-scheme`.
- All tokens defined in `tokens.css` with `:root.dark` overrides.

## Migration Guide

Replace ad-hoc utilities with semantic roles:

```tsx
// Before
<h1 className="text-4xl font-bold tracking-tight">Title</h1>

// After
<h1 className={roleClasses.h1}>Title</h1>
```