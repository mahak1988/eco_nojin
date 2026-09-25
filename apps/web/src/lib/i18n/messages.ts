import { readFile } from 'node:fs/promises';
import path from 'node:path';

type Json = Record<string, unknown>;

async function readJson(file: string): Promise<Json> {
  try {
    const content = await readFile(file, 'utf8');
    return JSON.parse(content.replace(/^\uFEFF/, '')) as Json;
  } catch {
    return {};
  }
}

function getMeta(obj: Json): Json {
  const meta = obj.meta as Json | undefined;
  return meta ?? { machineTranslated: false, fallbackLocale: null };
}

/**
 * Deep-merges catalogue layers so a requested locale can override the
 * canonical English catalogue without hiding its own namespaces.
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
 * Loads messages for a locale with English as the canonical fallback.
 * When a catalogue is still machine-translated, the `meta.machineTranslated` flag
 * is preserved so the UI can label it honestly.
 */
export async function loadMessages(locale: string): Promise<Json> {
  const dir = path.join(process.cwd(), 'messages');
  const en = await readJson(path.join(dir, 'en.json'));
  if (locale === 'en') {
    return { ...en, meta: { machineTranslated: false, fallbackLocale: null } };
  }

  const requested = await readJson(path.join(dir, `${locale}.json`));
  const merged = deepMerge(en, requested);
  merged.meta =
    locale === 'fa' ? { machineTranslated: false, fallbackLocale: null } : getMeta(requested);
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
