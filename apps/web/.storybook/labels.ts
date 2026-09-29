import type { StateLabels } from '../src/components/ui/StateSlot';
import { type AppLocale, defaultLocale, locales } from '../src/i18n/routing';

/**
 * Sample strings for the stories.
 *
 * Everything in this file is a *fixture*: the strings a component would be given
 * by a page that had already resolved them from the message catalogue. They are
 * not product copy, and they are not a second copy of `messages/*.json`. The
 * primitives take every label as a prop precisely so that a component library
 * ships no translatable strings of its own, and a story that inlined a label
 * would be asserting the opposite of the rule the stories exist to demonstrate.
 * Do not "fix" these by wiring them to the catalogue — that is the page's job,
 * and the stories show the contract it has to satisfy.
 *
 * They live here, once, rather than in the twenty story files for two reasons.
 * `check-ui-kit.mjs` reads every `.tsx` under `src/components/ui` and fails on
 * a Persian literal in a JSX text position or in a `label=` prop, so a fixture
 * written inline would be read as a component carrying untranslatable copy. And
 * a reviewer switching the toolbar to `fa` needs the strings to follow, which
 * they can only do if there is one place to switch.
 *
 * `fa` and `en` are written out because those are the two the review has to be
 * possible in: `fa` is the platform default and the only RTL the design was drawn
 * for, and `en` is the one every reader of the repository reads. The other twelve
 * locales fall back to `en` for their *strings* while the toolbar still sets
 * `lang` and `dir` for them, which is what makes their script, direction and
 * metrics exercisable; that fallback is a limitation of the fixture set, not of
 * the components.
 */

const FA: StateLabels = {
  loading: 'در حال بارگذاری…',
  empty: 'هنوز داده‌ای ثبت نشده است',
  error: 'دریافت داده ممکن نشد',
  partial: 'تنها بخشی از داده نمایش داده می‌شود',
  offline: 'شما آفلاین هستید؛ داده‌های ذخیره‌شده نشان داده می‌شود',
  action: 'تلاش دوباره',
};

const EN: StateLabels = {
  loading: 'Loading…',
  empty: 'Nothing recorded yet',
  error: 'The data could not be loaded',
  partial: 'Only part of the data is shown',
  offline: 'You are offline; showing what is stored on this device',
  action: 'Try again',
};

const CATALOGUE: Record<string, StateLabels> = { fa: FA, en: EN };

/** The five states `StateSlot` renders, in the order the master plan lists them. */
export const STATE_ORDER = ['loading', 'empty', 'error', 'partial', 'offline'] as const;

export type StateName = (typeof STATE_ORDER)[number];

/** The locale the preview is currently rendering, as the decorator set it. */
export function currentLocale(): AppLocale {
  const lang = typeof document === 'undefined' ? null : document.documentElement.lang;
  return locales.includes(lang as AppLocale) ? (lang as AppLocale) : defaultLocale;
}

export function stateLabels(locale: AppLocale = currentLocale()): StateLabels {
  return CATALOGUE[locale] ?? EN;
}

/** The `detail` line that explains a partial result, e.g. "showing 3 of 51". */
const PARTIAL_DETAIL: Record<string, string> = {
  fa: 'نمایش ۳ مورد از ۵۱',
  en: 'Showing 3 of 51',
};

export function partialDetail(locale: AppLocale = currentLocale()): string {
  return PARTIAL_DETAIL[locale] ?? PARTIAL_DETAIL.en;
}

/** A representative filled dataset, used wherever a story needs real content. */
export const SAMPLE_ROWS = [
  { id: 'r-1', site: 'Urmia lake north', ndvi: 0.62, moisture: 41.8 },
  { id: 'r-2', site: 'Zayandeh Rud', ndvi: 0.38, moisture: 12.4 },
  { id: 'r-3', site: 'Alborz ridge', ndvi: 0.81, moisture: 55.1 },
] as const;
