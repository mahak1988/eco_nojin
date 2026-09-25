import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { locales } from '@/i18n/routing';
import { loadMessages } from '@/lib/i18n/messages';
import type { AdminResult } from './admin-server';

/**
 * Local, verifiable sources for the console pages.
 *
 * Every path is repository-relative so the console shows the same reference a
 * reviewer or auditor would use. Everything is read from files that ship with
 * the application. Nothing is synthesised: if a file is missing or unreadable
 * the loader reports an honest failure instead of an empty inventory.
 */

const APP_PREFIX = 'apps/web/';

export const TOKENS_JSON_PATH = `${APP_PREFIX}tokens/dtcg.json`;
export const TOKENS_CSS_PATH = `${APP_PREFIX}tokens/variables.css`;
export const GLOBALS_CSS_PATH = `${APP_PREFIX}src/app/globals.css`;
export const MESSAGES_GLOB_PATH = `${APP_PREFIX}messages/*.json`;

export interface AdminTokenRow {
  id: string;
  group: string;
  type: string;
  value: string;
  description: string;
}

export interface AdminCssVariableRow {
  id: string;
  token: string;
  value: string;
  file: string;
}

export interface AdminCssStateRow {
  id: string;
  selector: string;
  file: string;
}

export interface AdminLocaleRow {
  id: string;
  locale: string;
  ownKeys: number;
  effectiveKeys: number;
  missingKeys: number;
  machineTranslated: boolean;
  fallbackLocale: string | null;
}

function flatten(value: unknown, prefix = ''): string[] {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return prefix === '' ? [] : [prefix];
  }
  return Object.entries(value as Record<string, unknown>).flatMap(([key, child]) =>
    flatten(child, prefix === '' ? key : `${prefix}.${key}`),
  );
}

async function readText(relativePath: string): Promise<AdminResult<string>> {
  const appPath = relativePath.startsWith(APP_PREFIX)
    ? relativePath.slice(APP_PREFIX.length)
    : relativePath;
  try {
    const content = await readFile(path.join(process.cwd(), appPath), 'utf8');
    return { ok: true, data: content, status: 200 };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : String(error),
      status: 0,
    };
  }
}

/** Flattens the W3C DTCG document into one row per `$value` leaf. */
export async function readDesignTokens(): Promise<AdminResult<AdminTokenRow[]>> {
  const file = await readText(TOKENS_JSON_PATH);
  if (!file.ok) return file;

  let parsed: unknown;
  try {
    parsed = JSON.parse(file.data);
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : String(error),
      status: 0,
    };
  }

  const rows: AdminTokenRow[] = [];
  const walk = (node: unknown, pathParts: string[], description: string) => {
    if (!node || typeof node !== 'object' || Array.isArray(node)) return;
    const record = node as Record<string, unknown>;
    if ('$value' in record) {
      const id = pathParts.join('.');
      const raw = record.$value;
      rows.push({
        id,
        group: pathParts[0] ?? '',
        type: typeof record.$type === 'string' ? record.$type : '',
        value: Array.isArray(raw) ? raw.join(', ') : String(raw),
        description: typeof record.$description === 'string' ? record.$description : description,
      });
      return;
    }
    for (const [key, child] of Object.entries(record)) {
      if (key.startsWith('$')) continue;
      const childDescription =
        typeof child === 'object' && child !== null && !Array.isArray(child)
          ? (child as Record<string, unknown>).$description
          : undefined;
      walk(
        child,
        [...pathParts, key],
        typeof childDescription === 'string' ? childDescription : description,
      );
    }
  };
  walk(parsed, [], '');

  return { ok: true, data: rows, status: 200 };
}

/** Reads the custom properties a stylesheet actually declares. */
export async function readCssVariables(
  relativePath: string,
): Promise<AdminResult<AdminCssVariableRow[]>> {
  const file = await readText(relativePath);
  if (!file.ok) return file;

  const rows: AdminCssVariableRow[] = [];
  const pattern = /(--[a-zA-Z0-9-]+)\s*:\s*([^;]+);/g;
  let match = pattern.exec(file.data);
  while (match !== null) {
    rows.push({
      id: `${relativePath}#${match[1]}`,
      token: match[1],
      value: match[2].trim().replace(/\s+/g, ' '),
      file: relativePath,
    });
    match = pattern.exec(file.data);
  }

  return { ok: true, data: rows, status: 200 };
}

/** Reads the state hooks a stylesheet actually exposes. */
export async function readCssStates(
  relativePath: string,
): Promise<AdminResult<AdminCssStateRow[]>> {
  const file = await readText(relativePath);
  if (!file.ok) return file;

  const rows: AdminCssStateRow[] = [];
  const pattern = /(\.[a-zA-Z0-9_-]+[^{}]*\[data-state="([^"]+)"\][^{}]*)\{/g;
  let match = pattern.exec(file.data);
  while (match !== null) {
    rows.push({
      id: `${relativePath}#${match[2]}`,
      selector: `${match[1].trim()}`.replace(/\s+/g, ' '),
      file: relativePath,
    });
    match = pattern.exec(file.data);
  }

  return { ok: true, data: rows, status: 200 };
}

/**
 * Locale coverage. `effectiveKeys` comes from the real runtime loader
 * (`loadMessages`), so the console reports what the application actually
 * serves rather than a re-implemented approximation of it.
 */
export async function readLocaleCoverage(): Promise<AdminResult<AdminLocaleRow[]>> {
  const rows: AdminLocaleRow[] = [];
  const reference = new Set(
    flatten(await loadMessages('fa')).filter((key) => !key.startsWith('meta')),
  );

  for (const locale of locales) {
    const own = await readText(`${APP_PREFIX}messages/${locale}.json`);
    if (!own.ok) return own;

    let ownKeys = 0;
    try {
      ownKeys = flatten(JSON.parse(own.data)).filter((key) => !key.startsWith('meta')).length;
    } catch (error) {
      return {
        ok: false,
        error: error instanceof Error ? error.message : String(error),
        status: 0,
      };
    }

    const messages = await loadMessages(locale);
    const meta = (messages.meta ?? {}) as Record<string, unknown>;
    const effective = flatten(messages).filter((key) => !key.startsWith('meta'));
    const effectiveSet = new Set(effective);

    rows.push({
      id: locale,
      locale,
      ownKeys,
      effectiveKeys: effective.length,
      missingKeys: [...reference].filter((key) => !effectiveSet.has(key)).length,
      machineTranslated: meta.machineTranslated === true,
      fallbackLocale: typeof meta.fallbackLocale === 'string' ? meta.fallbackLocale : null,
    });
  }

  return { ok: true, data: rows, status: 200 };
}
