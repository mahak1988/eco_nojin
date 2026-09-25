import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { locales } from '@/i18n/routing';

type Catalogue = Record<string, unknown>;

export interface LocaleCoverageRow {
  locale: string;
  ownKeys: number;
  englishKeys: number;
  effectiveKeys: number;
  fromEnglish: number;
  machineTranslated: boolean;
  fallbackLocale: string | null;
}

export interface ChainStep {
  id: string;
  token: string;
  keys: number | null;
  source: string;
}

export interface LocaleFallbackReport {
  current: string;
  merge: string;
  origin: string;
  coverage: LocaleCoverageRow[];
  steps: ChainStep[];
  machineTranslated: boolean;
  fallbackLocale: string | null;
}

function flatten(catalogue: Catalogue, prefix = ''): string[] {
  return Object.entries(catalogue).flatMap(([key, value]) => {
    const full = prefix ? `${prefix}.${key}` : key;
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      return flatten(value as Catalogue, full);
    }
    return [full];
  });
}

export function catalogueKeys(catalogue: Catalogue): Set<string> {
  return new Set(flatten(catalogue).filter((key) => !key.startsWith('meta')));
}

function meta(catalogue: Catalogue): { machineTranslated: boolean; fallbackLocale: string | null } {
  const raw = (catalogue.meta ?? {}) as Catalogue;
  return {
    machineTranslated: raw.machineTranslated === true,
    fallbackLocale: typeof raw.fallbackLocale === 'string' ? raw.fallbackLocale : null,
  };
}

async function readCatalogue(locale: string): Promise<Catalogue> {
  const file = path.join(process.cwd(), 'messages', `${locale}.json`);
  try {
    return JSON.parse((await readFile(file, 'utf8')).replace(/^\uFEFF/, '')) as Catalogue;
  } catch {
    return {};
  }
}

export async function getLocaleFallbackReport(requested: string): Promise<LocaleFallbackReport> {
  const english = await readCatalogue('en');
  const englishKeys = catalogueKeys(english);

  const coverage: LocaleCoverageRow[] = [];
  let requestedKeys = englishKeys;
  for (const locale of locales) {
    const catalogue = locale === 'en' ? english : await readCatalogue(locale);
    const own = catalogueKeys(catalogue);
    if (locale === requested) requestedKeys = own;
    const effective = new Set([...englishKeys, ...own]);
    coverage.push({
      locale,
      ownKeys: own.size,
      englishKeys: englishKeys.size,
      effectiveKeys: effective.size,
      fromEnglish: [...effective].filter((key) => !own.has(key)).length,
      ...meta(catalogue),
    });
  }

  const current = coverage.find((row) => row.locale === requested) ?? coverage[0];
  const effectiveKeys = new Set([...englishKeys, ...requestedKeys]);

  const steps: ChainStep[] = [
    {
      id: 'requested',
      token: `messages/${requested}.json`,
      keys: requestedKeys.size,
      source: 'src/lib/i18n/messages.ts',
    },
    {
      id: 'english',
      token: 'messages/en.json',
      keys: englishKeys.size,
      source: 'src/lib/i18n/messages.ts',
    },
    {
      id: 'merged',
      token: `${requested} → en`,
      keys: effectiveKeys.size,
      source: 'deepMerge(en, requested)',
    },
    {
      id: 'served',
      token: `en → ${requested}`,
      keys: [...effectiveKeys].filter((key) => !requestedKeys.has(key)).length,
      source: 'loadMessages()',
    },
  ];

  return {
    current: current?.locale ?? requested,
    merge: `deepMerge(await readJson('messages/en.json'), await readJson('messages/${requested}.json'))`,
    origin: 'src/lib/i18n/messages.ts · loadMessages()',
    coverage,
    steps,
    machineTranslated: current?.machineTranslated ?? false,
    fallbackLocale: current?.fallbackLocale ?? null,
  };
}
