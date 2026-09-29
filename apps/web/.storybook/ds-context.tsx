import type { Decorator } from '@storybook/react-vite';
import { type AppLocale, defaultLocale, isRtl, locales } from '../src/i18n/routing';

export { currentLocale } from './labels';

/**
 * Locale and colour scheme for the preview.
 *
 * The master plan makes this platform RTL-first and ships fourteen locales
 * across five scripts. A design system reviewed only in `en`/`light` is reviewed
 * in a small fraction of its states: `fa`, `ar` and `ur` mirror every inline
 * edge, `ur` moves the type to Nastaliq with a taller line height, `hi`/`bn`/`zh`
 * each name a different bundled family, and `light-dark()` swaps every colour
 * token at once. None of that is visible in a single fixed frame, so the locale
 * and the scheme are globals on the toolbar and every story inherits them
 * without a line of its own.
 */

/**
 * The language's own name for itself, from `Intl.DisplayNames`.
 *
 * Written out by hand this is fourteen strings to keep in step with
 * `routing.ts`; read from the platform it is always the name that language uses
 * for itself, which is also the only name a reviewer of that language reads.
 */
function nativeNameOf(locale: AppLocale): string {
  try {
    return new Intl.DisplayNames([locale], { type: 'language' }).of(locale) ?? locale;
  } catch {
    return locale;
  }
}

/** Toolbar values, with `fa` first because it is the platform default. */
export const LOCALE_ITEMS = locales.map((locale) => ({
  value: locale,
  title: `${locale} · ${nativeNameOf(locale)}`,
}));

export const SCHEME_ITEMS = [
  { value: 'light', title: 'Light' },
  { value: 'dark', title: 'Dark' },
];

export type ColourScheme = 'light' | 'dark';

export const globalTypes = {
  locale: {
    description: 'Locale — sets `lang`, `dir` and the per-script typography',
    defaultValue: defaultLocale,
    toolbar: { icon: 'globe', items: LOCALE_ITEMS, dynamicTitle: true },
  },
  scheme: {
    description: 'Colour scheme — the `light-dark()` half of every token',
    defaultValue: 'light',
    toolbar: { icon: 'paintbrush', items: SCHEME_ITEMS, dynamicTitle: true },
  },
};

export function resolveLocale(value: unknown): AppLocale {
  return locales.includes(value as AppLocale) ? (value as AppLocale) : defaultLocale;
}

export function resolveScheme(value: unknown): ColourScheme {
  return value === 'dark' ? 'dark' : 'light';
}

/**
 * Applies the locale and the scheme to the real document, not to a wrapper.
 *
 * The per-locale typography rules in `globals.css` are keyed off `html[lang=…]`
 * and `light-dark()` resolves against the used colour scheme, so a decorator
 * that only set attributes on a `<div>` would leave the font and the palette on
 * the document defaults while everything else mirrored. Setting
 * `document.documentElement` is what makes the preview behave like the route it
 * stands in for.
 *
 * A story may pin either value with `parameters: { ecoLocale, ecoScheme }`, so
 * an RTL-specific or dark-specific defect can be photographed deterministically
 * in a screenshot run rather than only by trusting the toolbar.
 */
export const withDocumentLocale: Decorator = (Story, context) => {
  const parameters = context.parameters as {
    ecoLocale?: string;
    ecoScheme?: ColourScheme;
  };
  const locale = resolveLocale(parameters.ecoLocale ?? context.globals.locale);
  const scheme = resolveScheme(parameters.ecoScheme ?? context.globals.scheme);

  const root = document.documentElement;
  root.setAttribute('lang', locale);
  root.setAttribute('dir', isRtl(locale) ? 'rtl' : 'ltr');
  // `light-dark()` reads the used colour scheme, not a class and not a
  // `prefers-color-scheme` query, so this single declaration is what turns the
  // dark half of the palette on.
  root.style.colorScheme = scheme;

  return <Story />;
};
