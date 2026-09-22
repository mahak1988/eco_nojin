import { readFile } from 'node:fs/promises';
import path from 'node:path';

type Json = Record<string, unknown>;

async function readJson(file: string): Promise<Json> {
  try {
    return JSON.parse(await readFile(file, 'utf8')) as Json;
  } catch {
    return {};
  }
}

function deepMerge(base: Json, over: Json): Json {
  const out: Json = { ...base };
  for (const [key, value] of Object.entries(over)) {
    const prev = out[key];
    if (
      prev &&
      value &&
      typeof prev === 'object' &&
      typeof value === 'object' &&
      !Array.isArray(prev) &&
      !Array.isArray(value)
    ) {
      out[key] = deepMerge(prev as Json, value as Json);
    } else {
      out[key] = value;
    }
  }
  return out;
}

/**
 * Loads messages for a locale. Non-default locales are merged over the fa base
 * (fallback chain: locale -> fa). When a catalogue is still machine-translated,
 * the `meta.machineTranslated` flag is preserved so the UI can label it honestly.
 */
export async function loadMessages(locale: string): Promise<Json> {
  const dir = path.join(process.cwd(), 'messages');
  const base = await readJson(path.join(dir, 'fa.json'));
  if (locale === 'fa') return base;
  const over = await readJson(path.join(dir, `${locale}.json`));
  const merged = deepMerge(base, over);
  const meta = (merged.meta as Json | undefined) ?? {};
  if (meta.machineTranslated !== true) {
    meta.machineTranslated = true;
    meta.fallbackLocale = 'fa';
  }
  merged.meta = meta;
  return merged;
}

export async function getLocaleMeta(
  locale: string,
): Promise<{ machineTranslated: boolean; fallbackLocale: string | null }> {
  const msgs = await loadMessages(locale);
  const meta = (msgs.meta as Json | undefined) ?? {};
  return {
    machineTranslated: meta.machineTranslated === true,
    fallbackLocale: (meta.fallbackLocale as string | null) ?? null,
  };
}
