// Internationalization configuration for the Eco Nojin frontend.

export const locales = [
  "ar",
  "bn",
  "de",
  "en",
  "es",
  "fa",
  "fr",
  "hi",
  "it",
  "ms",
  "pt",
  "ru",
  "ur",
  "zh"
] as const;

export type Locale = (typeof locales)[number];

export const directions: Record<Locale, "ltr" | "rtl"> = {
  "ar": "rtl",
  "bn": "ltr",
  "de": "ltr",
  "en": "ltr",
  "es": "ltr",
  "fa": "rtl",
  "fr": "ltr",
  "hi": "ltr",
  "it": "ltr",
  "ms": "ltr",
  "pt": "ltr",
  "ru": "ltr",
  "ur": "rtl",
  "zh": "ltr"
};

export const defaultLocale: Locale = "en";
