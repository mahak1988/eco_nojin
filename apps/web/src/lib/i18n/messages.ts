import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { unstable_noStore as noStore } from 'next/cache';

type Json = Record<string, unknown>;

async function readJson(file: string): Promise<Json> {
  try {
    return JSON.parse(await readFile(file, 'utf8')) as Json;
  } catch {
    return {};
  }
}

function getMeta(obj: Json): Json {
  const meta = obj.meta as Json | undefined;
  return meta ?? { machineTranslated: false, fallbackLocale: null };
}

/**
 * Deep-merges catalogue layers so a skeleton locale's partial namespace
 * (e.g. its own `common` object) never shadows keys that only exist in the
 * fa/en reference layers.
 */
function deepMerge(...layers: Json[]): Json {
  const out: Json = {};
  for (const layer of layers) {
    for (const [key, value] of Object.entries(layer)) {
      if (
        value &&
        typeof value === 'object' &&
        !Array.isArray(value) &&
        out[key] &&
        typeof out[key] === 'object' &&
        !Array.isArray(out[key])
      ) {
        out[key] = deepMerge(out[key] as Json, value as Json);
      } else {
        out[key] = value;
      }
    }
  }
  return out;
}

/**
 * Loads messages for a locale. Fallback chain: locale -> en -> fa.
 * When a catalogue is still machine-translated, the `meta.machineTranslated` flag
 * is preserved so the UI can label it honestly.
 */
export async function loadMessages(locale: string): Promise<Json> {
  noStore(); // Prevent build-time caching of locale data
  const dir = path.join(process.cwd(), 'messages');
  const fa = await readJson(path.join(dir, 'fa.json'));
  if (locale === 'fa') {
    const result = { ...fa };
    result.meta = { machineTranslated: false, fallbackLocale: null };
    return result;
  }

  const en = await readJson(path.join(dir, 'en.json'));
  if (locale === 'en') {
    const merged = deepMerge(fa, en);
    merged.meta = { machineTranslated: false, fallbackLocale: null };
    return merged;
  }

  const over = await readJson(path.join(dir, `${locale}.json`));
  const merged = deepMerge(fa, en, over);
  merged.meta = getMeta(over);
  return merged;
}

export async function getLocaleMeta(
  locale: string,
): Promise<{ machineTranslated: boolean; fallbackLocale: string | null }> {
  const msgs = await loadMessages(locale);
  const meta = getMeta(msgs);
  return {
    machineTranslated: meta.machineTranslated === true,
    fallbackLocale: (meta.fallbackLocale as string | null) ?? null,
  };
}
