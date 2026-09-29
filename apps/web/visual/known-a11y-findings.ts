/**
 * Accessibility findings that are known, unfixed, and *named*.
 *
 * `visual/specs/design-system.spec.ts` runs axe-core over every story and fails
 * on any finding that is not in this list. So:
 *
 *   - a new defect fails the run;
 *   - a defect fixed elsewhere in the tree does not, and the run prints which
 *     entries have stopped reproducing so they can be deleted from here;
 *   - every entry below is a defect that is real and currently open, and the
 *     screenshot of it is committed under `visual/__screenshots__/`.
 *
 * This file is the deliberate act. Deleting an entry is how a finding is
 * accepted; a run that has silently forgotten one is not possible, because
 * `visual/a11y-report.json` records every finding the last run saw, known or not,
 * and a finding that no longer reproduces is reported as `cleared`.
 *
 * Nothing here is worked around in a story. Every one of these was produced by
 * rendering the component the way a page renders it, and every `target` is the
 * selector axe-core named, so the entry stops matching the moment the defect is
 * gone.
 *
 * Generated from the run of 2026-09-29 and reviewed by hand; the note on each
 * entry says what the defect is and what fixes it.
 */
export interface KnownFinding {
  /** The Storybook story id, or `<id> (<locale> / <scheme>)` for a matrix frame. */
  story: string;
  /** The axe-core rule id. */
  rule: string;
  /** The CSS selector axe named, so the entry matches a moving DOM. */
  target: string;
  /** What the defect is and what fixes it. */
  note: string;
}

export const KNOWN_A11Y_FINDINGS: KnownFinding[] = [
  {
    story: 'data-datatable--alignment-in-rtl (fa / light)',
    rule: 'color-contrast',
    target: 'tr:nth-child(4) > .text-start:nth-child(4) > span',
    note: '`Badge.tsx` tone="bad" is `text-clay bg-clay/8`. `--clay` is #ac543f and the 8% tint over `--surface` is #eee7e0, which measures 4.18:1 at 12-14px. `--clay` was re-solved to oklch(0.735) in dark mode to reach 4.5:1 on `--surface`; the tinted background is a different surface and lands under the floor. Fix: one step down on the text, or a darker tint.',
  },
  {
    story: 'data-datatable--alignment-in-rtl',
    rule: 'color-contrast',
    target: 'tr:nth-child(4) > .text-start:nth-child(4) > span',
    note: '`Badge.tsx` tone="bad" is `text-clay bg-clay/8`. `--clay` is #ac543f and the 8% tint over `--surface` is #eee7e0, which measures 4.18:1 at 12-14px. `--clay` was re-solved to oklch(0.735) in dark mode to reach 4.5:1 on `--surface`; the tinted background is a different surface and lands under the floor. Fix: one step down on the text, or a darker tint.',
  },
  {
    story: 'data-datatable--controlled-sort',
    rule: 'color-contrast',
    target: 'tr:nth-child(1) > .text-start:nth-child(4) > span',
    note: '`Badge.tsx` tone="bad" is `text-clay bg-clay/8`. `--clay` is #ac543f and the 8% tint over `--surface` is #eee7e0, which measures 4.18:1 at 12-14px. `--clay` was re-solved to oklch(0.735) in dark mode to reach 4.5:1 on `--surface`; the tinted background is a different surface and lands under the floor. Fix: one step down on the text, or a darker tint.',
  },
  {
    story: 'data-datatable--default',
    rule: 'color-contrast',
    target: 'tr:nth-child(4) > .text-start:nth-child(4) > span',
    note: '`Badge.tsx` tone="bad" is `text-clay bg-clay/8`. `--clay` is #ac543f and the 8% tint over `--surface` is #eee7e0, which measures 4.18:1 at 12-14px. `--clay` was re-solved to oklch(0.735) in dark mode to reach 4.5:1 on `--surface`; the tinted background is a different surface and lands under the floor. Fix: one step down on the text, or a darker tint.',
  },
  {
    story: 'data-datatable--densities',
    rule: 'color-contrast',
    target:
      'div:nth-child(1) > .eco-scroll > div > table > tbody > tr:nth-child(4) > .text-start:nth-child(4) > span',
    note: '`Badge.tsx` tone="bad" is `text-clay bg-clay/8`. `--clay` is #ac543f and the 8% tint over `--surface` is #eee7e0, which measures 4.18:1 at 12-14px. `--clay` was re-solved to oklch(0.735) in dark mode to reach 4.5:1 on `--surface`; the tinted background is a different surface and lands under the floor. Fix: one step down on the text, or a darker tint.',
  },
  {
    story: 'data-datatable--densities',
    rule: 'color-contrast',
    target:
      'div:nth-child(2) > .eco-scroll > div > table > tbody > tr:nth-child(4) > .text-start:nth-child(4) > span',
    note: '`Badge.tsx` tone="bad" is `text-clay bg-clay/8`. `--clay` is #ac543f and the 8% tint over `--surface` is #eee7e0, which measures 4.18:1 at 12-14px. `--clay` was re-solved to oklch(0.735) in dark mode to reach 4.5:1 on `--surface`; the tinted background is a different surface and lands under the floor. Fix: one step down on the text, or a darker tint.',
  },
  {
    story: 'data-datatable--densities',
    rule: 'color-contrast',
    target:
      'div:nth-child(3) > .eco-scroll > div > table > tbody > tr:nth-child(4) > .text-start:nth-child(4) > span',
    note: '`Badge.tsx` tone="bad" is `text-clay bg-clay/8`. `--clay` is #ac543f and the 8% tint over `--surface` is #eee7e0, which measures 4.18:1 at 12-14px. `--clay` was re-solved to oklch(0.735) in dark mode to reach 4.5:1 on `--surface`; the tinted background is a different surface and lands under the floor. Fix: one step down on the text, or a darker tint.',
  },
  {
    story: 'data-datatable--states',
    rule: 'color-contrast',
    target: 'tr:nth-child(4) > .text-start:nth-child(4) > span',
    note: '`Badge.tsx` tone="bad" is `text-clay bg-clay/8`. `--clay` is #ac543f and the 8% tint over `--surface` is #eee7e0, which measures 4.18:1 at 12-14px. `--clay` was re-solved to oklch(0.735) in dark mode to reach 4.5:1 on `--surface`; the tinted background is a different surface and lands under the floor. Fix: one step down on the text, or a darker tint.',
  },
  {
    story: 'data-progress--default',
    rule: 'aria-progressbar-name',
    target: 'div[role="progressbar"]',
    note: '`Progress.tsx` renders `label` as a sibling <span> above the bar and never as `aria-label`/`aria-labelledby` on the `role="progressbar"` element, so the bar has no accessible name. Fix: put the visible label in an id and reference it with `aria-labelledby`, and pass it through even when `hideLabel` is set.',
  },
  {
    story: 'data-progress--indeterminate',
    rule: 'aria-progressbar-name',
    target: 'div:nth-child(1) > div > div[role="progressbar"]',
    note: '`Progress.tsx` renders `label` as a sibling <span> above the bar and never as `aria-label`/`aria-labelledby` on the `role="progressbar"` element, so the bar has no accessible name. Fix: put the visible label in an id and reference it with `aria-labelledby`, and pass it through even when `hideLabel` is set.',
  },
  {
    story: 'data-progress--partial-value',
    rule: 'aria-progressbar-name',
    target: 'div[role="progressbar"]',
    note: '`Progress.tsx` renders `label` as a sibling <span> above the bar and never as `aria-label`/`aria-labelledby` on the `role="progressbar"` element, so the bar has no accessible name. Fix: put the visible label in an id and reference it with `aria-labelledby`, and pass it through even when `hideLabel` is set.',
  },
  {
    story: 'data-progress--sizes',
    rule: 'aria-progressbar-name',
    target:
      'div:nth-child(1) > div > div[role="progressbar"][aria-valuemin="0"][aria-valuemax="100"]',
    note: '`Progress.tsx` renders `label` as a sibling <span> above the bar and never as `aria-label`/`aria-labelledby` on the `role="progressbar"` element, so the bar has no accessible name. Fix: put the visible label in an id and reference it with `aria-labelledby`, and pass it through even when `hideLabel` is set.',
  },
  {
    story: 'data-progress--sizes',
    rule: 'aria-progressbar-name',
    target:
      'div:nth-child(2) > div > div[role="progressbar"][aria-valuemin="0"][aria-valuemax="100"]',
    note: '`Progress.tsx` renders `label` as a sibling <span> above the bar and never as `aria-label`/`aria-labelledby` on the `role="progressbar"` element, so the bar has no accessible name. Fix: put the visible label in an id and reference it with `aria-labelledby`, and pass it through even when `hideLabel` is set.',
  },
  {
    story: 'data-progress--sizes',
    rule: 'aria-progressbar-name',
    target:
      'div:nth-child(3) > div > div[role="progressbar"][aria-valuemin="0"][aria-valuemax="100"]',
    note: '`Progress.tsx` renders `label` as a sibling <span> above the bar and never as `aria-label`/`aria-labelledby` on the `role="progressbar"` element, so the bar has no accessible name. Fix: put the visible label in an id and reference it with `aria-labelledby`, and pass it through even when `hideLabel` is set.',
  },
  {
    story: 'data-progress--states',
    rule: 'aria-progressbar-name',
    target: 'div[role="progressbar"]',
    note: '`Progress.tsx` renders `label` as a sibling <span> above the bar and never as `aria-label`/`aria-labelledby` on the `role="progressbar"` element, so the bar has no accessible name. Fix: put the visible label in an id and reference it with `aria-labelledby`, and pass it through even when `hideLabel` is set.',
  },
  {
    story: 'data-progress--tones',
    rule: 'aria-progressbar-name',
    target:
      'div:nth-child(1) > div > div[role="progressbar"][aria-valuemin="0"][aria-valuemax="100"]',
    note: '`Progress.tsx` renders `label` as a sibling <span> above the bar and never as `aria-label`/`aria-labelledby` on the `role="progressbar"` element, so the bar has no accessible name. Fix: put the visible label in an id and reference it with `aria-labelledby`, and pass it through even when `hideLabel` is set.',
  },
  {
    story: 'data-progress--tones',
    rule: 'aria-progressbar-name',
    target:
      'div:nth-child(2) > div > div[role="progressbar"][aria-valuemin="0"][aria-valuemax="100"]',
    note: '`Progress.tsx` renders `label` as a sibling <span> above the bar and never as `aria-label`/`aria-labelledby` on the `role="progressbar"` element, so the bar has no accessible name. Fix: put the visible label in an id and reference it with `aria-labelledby`, and pass it through even when `hideLabel` is set.',
  },
  {
    story: 'data-progress--tones',
    rule: 'aria-progressbar-name',
    target:
      'div:nth-child(3) > div > div[role="progressbar"][aria-valuemin="0"][aria-valuemax="100"]',
    note: '`Progress.tsx` renders `label` as a sibling <span> above the bar and never as `aria-label`/`aria-labelledby` on the `role="progressbar"` element, so the bar has no accessible name. Fix: put the visible label in an id and reference it with `aria-labelledby`, and pass it through even when `hideLabel` is set.',
  },
  {
    story: 'data-progress--tones',
    rule: 'aria-progressbar-name',
    target:
      'div:nth-child(4) > div > div[role="progressbar"][aria-valuemin="0"][aria-valuemax="100"]',
    note: '`Progress.tsx` renders `label` as a sibling <span> above the bar and never as `aria-label`/`aria-labelledby` on the `role="progressbar"` element, so the bar has no accessible name. Fix: put the visible label in an id and reference it with `aria-labelledby`, and pass it through even when `hideLabel` is set.',
  },
  {
    story: 'navigation-tabs--caller-owned-panel',
    rule: 'color-contrast',
    target: '.num',
    note: '`Tabs.tsx` renders the `hint` with `text-ink-faint` on the `--surface` tab bar. `--ink-faint` is #6c7676 on #f4f4ee = 4.23:1 at 16px, and 4.25:1 where the hint is highlighted. `check-contrast.mjs` does not cover it because it is a component pairing, not a palette pair. Fix: `text-ink-soft`, or a dedicated hint step.',
  },
  {
    story: 'navigation-tabs--default',
    rule: 'color-contrast',
    target: '.num',
    note: '`Tabs.tsx` renders the `hint` with `text-ink-faint` on the `--surface` tab bar. `--ink-faint` is #6c7676 on #f4f4ee = 4.23:1 at 16px, and 4.25:1 where the hint is highlighted. `check-contrast.mjs` does not cover it because it is a component pairing, not a palette pair. Fix: `text-ink-soft`, or a dedicated hint step.',
  },
  {
    story: 'navigation-tabs--densities',
    rule: 'color-contrast',
    target: '#_r_0_-measurements > .num',
    note: '`Tabs.tsx` renders the `hint` with `text-ink-faint` on the `--surface` tab bar. `--ink-faint` is #6c7676 on #f4f4ee = 4.23:1 at 16px, and 4.25:1 where the hint is highlighted. `check-contrast.mjs` does not cover it because it is a component pairing, not a palette pair. Fix: `text-ink-soft`, or a dedicated hint step.',
  },
  {
    story: 'navigation-tabs--densities',
    rule: 'color-contrast',
    target: '#_r_1_-measurements > .num',
    note: '`Tabs.tsx` renders the `hint` with `text-ink-faint` on the `--surface` tab bar. `--ink-faint` is #6c7676 on #f4f4ee = 4.23:1 at 16px, and 4.25:1 where the hint is highlighted. `check-contrast.mjs` does not cover it because it is a component pairing, not a palette pair. Fix: `text-ink-soft`, or a dedicated hint step.',
  },
  {
    story: 'navigation-tabs--densities',
    rule: 'color-contrast',
    target: '#_r_2_-measurements > .num',
    note: '`Tabs.tsx` renders the `hint` with `text-ink-faint` on the `--surface` tab bar. `--ink-faint` is #6c7676 on #f4f4ee = 4.23:1 at 16px, and 4.25:1 where the hint is highlighted. `check-contrast.mjs` does not cover it because it is a component pairing, not a palette pair. Fix: `text-ink-soft`, or a dedicated hint step.',
  },
  {
    story: 'navigation-tabs--in-persian',
    rule: 'color-contrast',
    target: '.num',
    note: '`Tabs.tsx` renders the `hint` with `text-ink-faint` on the `--surface` tab bar. `--ink-faint` is #6c7676 on #f4f4ee = 4.23:1 at 16px, and 4.25:1 where the hint is highlighted. `check-contrast.mjs` does not cover it because it is a component pairing, not a palette pair. Fix: `text-ink-soft`, or a dedicated hint step.',
  },
  {
    story: 'navigation-tabs--states',
    rule: 'color-contrast',
    target: '.num',
    note: '`Tabs.tsx` renders the `hint` with `text-ink-faint` on the `--surface` tab bar. `--ink-faint` is #6c7676 on #f4f4ee = 4.23:1 at 16px, and 4.25:1 where the hint is highlighted. `check-contrast.mjs` does not cover it because it is a component pairing, not a palette pair. Fix: `text-ink-soft`, or a dedicated hint step.',
  },
  {
    story: 'overlays-commandpalette--no-commands',
    rule: 'aria-required-children',
    target: '#command-palette-list',
    note: '`CommandPalette.tsx` renders `role="listbox"` unconditionally, including when `items` is empty, so the listbox has no `role="option"` children. Fix: do not render the listbox when the filtered list is empty.',
  },
  {
    story: 'primitives-badge--in-persian',
    rule: 'color-contrast',
    target: 'div:nth-child(1) > .eco-row > span:nth-child(4)',
    note: '`Badge.tsx` tone="bad" is `text-clay bg-clay/8`. `--clay` is #ac543f and the 8% tint over `--surface` is #eee7e0, which measures 4.18:1 at 12-14px. `--clay` was re-solved to oklch(0.735) in dark mode to reach 4.5:1 on `--surface`; the tinted background is a different surface and lands under the floor. Fix: one step down on the text, or a darker tint.',
  },
  {
    story: 'primitives-badge--in-persian',
    rule: 'color-contrast',
    target: 'div:nth-child(2) > .eco-row > span:nth-child(4)',
    note: '`Badge.tsx` tone="bad" is `text-clay bg-clay/8`. `--clay` is #ac543f and the 8% tint over `--surface` is #eee7e0, which measures 4.18:1 at 12-14px. `--clay` was re-solved to oklch(0.735) in dark mode to reach 4.5:1 on `--surface`; the tinted background is a different surface and lands under the floor. Fix: one step down on the text, or a darker tint.',
  },
  {
    story: 'primitives-badge--in-persian',
    rule: 'color-contrast',
    target: 'div:nth-child(3) > .eco-row > span:nth-child(4)',
    note: '`Badge.tsx` tone="bad" is `text-clay bg-clay/8`. `--clay` is #ac543f and the 8% tint over `--surface` is #eee7e0, which measures 4.18:1 at 12-14px. `--clay` was re-solved to oklch(0.735) in dark mode to reach 4.5:1 on `--surface`; the tinted background is a different surface and lands under the floor. Fix: one step down on the text, or a darker tint.',
  },
  {
    story: 'primitives-badge--tones',
    rule: 'color-contrast',
    target: 'div:nth-child(1) > .eco-row > span:nth-child(2)',
    note: '`Badge.tsx` tone="info" is `text-water bg-water/8`. `--water` is #4489ae and the 8% tint over `--surface` is #e6ebe9, which measures 3.2:1 at 14px. The palette pair `--water` on `--surface` passes `check-contrast.mjs`; the tint background is what fails. Fix: raise the tint step, darken the text step, or use the solid token as the background with `--on-action` as the text.',
  },
  {
    story: 'primitives-badge--tones',
    rule: 'color-contrast',
    target: 'div:nth-child(1) > .eco-row > span:nth-child(5)',
    note: '`Badge.tsx` tone="bad" is `text-clay bg-clay/8`. `--clay` is #ac543f and the 8% tint over `--surface` is #eee7e0, which measures 4.18:1 at 12-14px. `--clay` was re-solved to oklch(0.735) in dark mode to reach 4.5:1 on `--surface`; the tinted background is a different surface and lands under the floor. Fix: one step down on the text, or a darker tint.',
  },
  {
    story: 'primitives-badge--tones',
    rule: 'color-contrast',
    target: 'div:nth-child(2) > .eco-row > span:nth-child(2)',
    note: '`Badge.tsx` tone="info" is `text-water bg-water/8`. `--water` is #4489ae and the 8% tint over `--surface` is #e6ebe9, which measures 3.2:1 at 14px. The palette pair `--water` on `--surface` passes `check-contrast.mjs`; the tint background is what fails. Fix: raise the tint step, darken the text step, or use the solid token as the background with `--on-action` as the text.',
  },
  {
    story: 'primitives-badge--tones',
    rule: 'color-contrast',
    target: 'div:nth-child(2) > .eco-row > span:nth-child(5)',
    note: '`Badge.tsx` tone="bad" is `text-clay bg-clay/8`. `--clay` is #ac543f and the 8% tint over `--surface` is #eee7e0, which measures 4.18:1 at 12-14px. `--clay` was re-solved to oklch(0.735) in dark mode to reach 4.5:1 on `--surface`; the tinted background is a different surface and lands under the floor. Fix: one step down on the text, or a darker tint.',
  },
  {
    story: 'primitives-button--variants (fa / dark)',
    rule: 'color-contrast',
    target: 'div:nth-child(1) > .eco-row > button[type="button"]:nth-child(8) > span',
    note: '`Button.tsx` variant="danger" is `bg-clay text-on-action`. `--clay` darkens to oklch(0.735) in dark mode — a light background — while `--on-action` is a single near-white value with no dark counterpart, giving #fbfcf9 on #e78a45 = 2.51:1. The same pairing is the only failing one in the dark matrix. Fix: give `--on-action` a dark half, or give the danger variant a text token solved against the dark `--clay`.',
  },
];
