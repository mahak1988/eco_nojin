import { readdirSync, statSync } from 'node:fs';
import path from 'node:path';

import { catalogFallbackPaths, PAGE_CATALOG } from './lib/domains/page-catalog.ts';

const APP_ROOT = path.join(import.meta.dirname, 'app', '[locale]');

function scan(dir, acc = []) {
  for (const name of readdirSync(dir)) {
    const full = path.join(dir, name);
    if (statSync(full).isDirectory()) {
      if (name.startsWith('_')) continue;
      scan(full, acc);
    } else if (name === 'page.tsx') {
      acc.push(full.replace(`${APP_ROOT}/`, ''));
    }
  }
  return acc;
}

const files = scan(APP_ROOT).filter(
  (f) => !f.startsWith('(catalog)/') && !f.startsWith('_not-found'),
);

const routeFileToLogical = (file) => {
  const dir = path.posix.dirname(file).replace(/^\.$/, '');
  return `/${dir}`
    .replace(/\[\[\.\.\.(\w+)\]\]/g, '{$1}')
    .replace(/\[\.\.\.(\w+)\]/g, '{$1}')
    .replace(/\[(\w+)\]/g, '{$1}')
    .replace(/\/\{\*?(\w+)\}/g, '/{$1}');
};

const patternToRegExp = (logical) => {
  const source = logical
    .replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    .replace(/\\\{\*(\w+)\\\}/g, '.+')
    .replace(/\\\{(\w+)\\\}/g, '[^/]+');
  return new RegExp(`^${source}$`);
};

const patterns = files.map((file) => ({
  file,
  matcher: patternToRegExp(routeFileToLogical(file)),
}));

for (const p of catalogFallbackPaths()) {
  const clash = patterns.filter((r) => r.matcher.test(p));
  if (clash.length > 0) {
    console.log(`fallback path ${p} is now served by:`);
    for (const c of clash) console.log(`  ${c.file}  -> ${routeFileToLogical(c.file)}`);
    const entry = PAGE_CATALOG.find((e) => e.path === p);
    console.log(`  entry: id=${entry?.id} status=${entry?.status} routeFile=${entry?.routeFile}`);
  }
}
