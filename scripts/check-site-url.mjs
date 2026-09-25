import { readdir, readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { join, relative } from 'node:path';

// Resolved from this file so the guard works from the repo root, from
// `apps/web`, and from CI regardless of the caller's working directory.
const PROJECT_ROOT = fileURLToPath(new URL('..', import.meta.url));
const SOURCE_ROOT = join(PROJECT_ROOT, 'apps/web/src');
const SITE_CONFIG = join(SOURCE_ROOT, 'config', 'site.ts');

/** Reserved documentation domains (RFC 2606) plus the `.test` TLD: never a real site. */
const PLACEHOLDER_ORIGIN = /https?:\/\/[^\s'"`)<>]*\bexample\.(?:org|com|net|test)\b/i;
const INLINE_ENV_READ = /process\.env\.NEXT_PUBLIC_SITE_URL/;

const isTestFile = (path) =>
  /\.(test|spec)\.[jt]sx?$/.test(path) || /[\\/](tests?|__tests__)[\\/]/.test(path);

const findings = [];

async function walk(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      await walk(path);
      continue;
    }
    if (!/\.[jt]sx?$/.test(entry.name) || path === SITE_CONFIG) continue;

    const content = await readFile(path, 'utf8');
    const shown = relative(PROJECT_ROOT, path);

    content.split('\n').forEach((line, index) => {
      const at = `${shown}:${index + 1}`;
      if (PLACEHOLDER_ORIGIN.test(line) && !isTestFile(path)) {
        findings.push(`${at} placeholder site origin — import SITE_URL from '@/config/site'`);
      }
      if (INLINE_ENV_READ.test(line)) {
        findings.push(
          `${at} inline NEXT_PUBLIC_SITE_URL read — only 'src/config/site.ts' may read it`,
        );
      }
    });
  }
}

try {
  await walk(SOURCE_ROOT);
} catch (error) {
  if (error.code === 'ENOENT') {
    console.error(`Site URL guard: source root not found at ${relative(PROJECT_ROOT, SOURCE_ROOT)}`);
    process.exit(1);
  }
  throw error;
}

try {
  const config = await readFile(SITE_CONFIG, 'utf8');
  if (!/export const SITE_URL\b/.test(config)) {
    findings.push("apps/web/src/config/site.ts: missing `export const SITE_URL`");
  }
} catch (error) {
  if (error.code === 'ENOENT') {
    findings.push('apps/web/src/config/site.ts: shared site URL module is missing');
  } else {
    throw error;
  }
}

if (findings.length > 0) {
  console.error(`Site URL guard failed with ${findings.length} finding(s):`);
  for (const finding of findings) console.error(`- ${finding}`);
  process.exit(1);
}

console.log('Site URL guard passed: no placeholder origins and no inline NEXT_PUBLIC_SITE_URL reads.');
