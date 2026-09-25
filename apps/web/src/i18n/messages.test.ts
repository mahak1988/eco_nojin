import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

const locales = [
  'fa',
  'en',
  'ar',
  'ur',
  'de',
  'es',
  'fr',
  'hi',
  'it',
  'ms',
  'pt',
  'ru',
  'zh',
  'bn',
];

describe('locale catalogue files', () => {
  it.each(locales)('%s is valid JSON with an object catalogue', (locale) => {
    const file = path.join(process.cwd(), 'messages', `${locale}.json`);
    const content = readFileSync(file, 'utf8').replace(/^\uFEFF/, '');
    const catalogue = JSON.parse(content) as Record<string, unknown>;

    expect(typeof catalogue).toBe('object');
    expect(catalogue.meta).toBeTruthy();
  });
});
