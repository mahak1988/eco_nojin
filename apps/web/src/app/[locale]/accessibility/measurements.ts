/**
 * The measurement record behind `/accessibility`.
 *
 * The accessibility statement is the one public page that must not hand-wave, and
 * the reason it is a data file rather than prose is that its two claims are
 * numbers produced by two gates that live in this repository:
 *
 *   - `scripts/check-contrast.mjs` — measures every foreground/background token
 *     pair `globals.css` declares, in both colour schemes, against the WCAG floor
 *     for that pair.
 *   - `scripts/check-font-coverage.mjs` — resolves the family each locale is
 *     mapped to and whether that family is shipped from this origin.
 *
 * Both are re-runnable. The commands are recorded next to each number so a
 * reader can reproduce the figure rather than take it on trust, and `MEASURED_AT`
 * is the date the record below was taken. When either gate changes its output,
 * this file changes with it: a statement that keeps claiming a stale number is
 * worse than one that says it does not know.
 *
 * Nothing here is asserted beyond what those two scripts printed. There is no
 * external audit, no assistive-technology user study, and no screen-reader check
 * in this repository, so `EXTERNAL_REVIEW` says so instead of implying otherwise.
 */

export interface Measurement {
  /** The gate that produced the figure, as a path from the repository root. */
  readonly script: string;
  /** The exact command, so the figure can be reproduced. */
  readonly command: string;
  /** ISO date the figure below was taken. */
  readonly measuredAt: string;
  /** Verbatim summary line the gate printed. */
  readonly summary: string;
  /** The figures, each a label/value pair the page renders. */
  readonly figures: readonly { readonly label: string; readonly value: string }[];
}

export const MEASURED_AT = '2026-09-29';

export const CONTRAST_MEASUREMENT: Measurement = {
  script: 'scripts/check-contrast.mjs',
  command: 'node scripts/check-contrast.mjs',
  measuredAt: MEASURED_AT,
  summary: 'all measured pairs meet their floor',
  figures: [
    { label: 'tokenPairs', value: '21' },
    { label: 'textFloor', value: '4.5' },
    { label: 'boundaryFloor', value: '3' },
    { label: 'hairlineFloor', value: '1' },
  ],
};

export const FONT_MEASUREMENT: Measurement = {
  script: 'scripts/check-font-coverage.mjs',
  command: 'node scripts/check-font-coverage.mjs',
  measuredAt: MEASURED_AT,
  summary: 'all 14 locales are served by a family bundled from this origin',
  figures: [
    { label: 'families', value: '7' },
    { label: 'files', value: '108' },
    { label: 'bytesOnDisk', value: '5070900' },
    { label: 'localesBundled', value: '14' },
    { label: 'localesTotal', value: '14' },
  ],
};

/**
 * The rows of the font table, straight from the gate's own locale listing.
 *
 * A locale appears in the fallback column when its mapped family is named in the
 * stylesheet but not shipped from this origin. The list is empty today, and the
 * table renders that emptiness as a fact rather than hiding the column.
 */
export const FONT_ROWS: readonly {
  readonly locale: string;
  readonly family: string;
  readonly faces: number;
  readonly bytes: number;
  readonly script: string;
  readonly shipped: boolean;
}[] = [
  { locale: 'fa', family: 'Vazirmatn', faces: 6, bytes: 95980, script: 'Arabic', shipped: true },
  {
    locale: 'ar',
    family: 'Vazirmatn',
    faces: 6,
    bytes: 95980,
    script: 'Arabic',
    shipped: true,
  },
  {
    locale: 'en',
    family: 'JetBrains Mono',
    faces: 2,
    bytes: 43028,
    script: 'Latin',
    shipped: true,
  },
  {
    locale: 'de',
    family: 'JetBrains Mono',
    faces: 2,
    bytes: 43028,
    script: 'Latin',
    shipped: true,
  },
  {
    locale: 'es',
    family: 'JetBrains Mono',
    faces: 2,
    bytes: 43028,
    script: 'Latin',
    shipped: true,
  },
  {
    locale: 'fr',
    family: 'JetBrains Mono',
    faces: 2,
    bytes: 43028,
    script: 'Latin',
    shipped: true,
  },
  {
    locale: 'it',
    family: 'JetBrains Mono',
    faces: 2,
    bytes: 43028,
    script: 'Latin',
    shipped: true,
  },
  {
    locale: 'ms',
    family: 'JetBrains Mono',
    faces: 2,
    bytes: 43028,
    script: 'Latin',
    shipped: true,
  },
  {
    locale: 'pt',
    family: 'JetBrains Mono',
    faces: 2,
    bytes: 43028,
    script: 'Latin',
    shipped: true,
  },
  {
    locale: 'ru',
    family: 'JetBrains Mono',
    faces: 2,
    bytes: 43028,
    script: 'Latin',
    shipped: true,
  },
  {
    locale: 'hi',
    family: 'Noto Sans Devanagari',
    faces: 1,
    bytes: 121192,
    script: 'Devanagari',
    shipped: true,
  },
  {
    locale: 'bn',
    family: 'Noto Sans Bengali',
    faces: 1,
    bytes: 107720,
    script: 'Bengali',
    shipped: true,
  },
  {
    locale: 'zh',
    family: 'Noto Sans SC',
    faces: 97,
    bytes: 4463920,
    script: 'CJK',
    shipped: true,
  },
  {
    locale: 'ur',
    family: 'Noto Nastaliq Urdu',
    faces: 1,
    bytes: 239060,
    script: 'Nastaliq',
    shipped: true,
  },
];

/** The two channels this page's inclusive claim is about, as the gateway sees them. */
export const INCLUSIVE_CHANNELS = [
  { id: 'ussd', path: '/api/v1/ussd/status' },
  { id: 'voice', path: '/api/v1/voice/status' },
  { id: 'voice-languages', path: '/api/v1/voice/languages' },
] as const;

/**
 * What this page cannot support, stated once and reused by the report.
 *
 * Every entry is a thing a reader would reasonably expect an accessibility
 * statement to cover. Naming the gap is the only way a statement stays honest
 * once an external review has not happened.
 */
export const EXTERNAL_REVIEW = {
  audit: false,
  assistiveTechnologyStudy: false,
  screenReaderAutomation: false,
  conformanceLevel: null,
} as const;
