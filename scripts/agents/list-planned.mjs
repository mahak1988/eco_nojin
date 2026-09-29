#!/usr/bin/env node
/**
 * list-planned.mjs — queue helper for the page-completion agents.
 *
 * Usage: node scripts/agents/list-planned.mjs <domain>
 *   domain: public | system | admin | research
 * Prints one path per line: the catalogue entries of that domain that are still
 * `planned` (no route file yet). The agents take the first line as their unit.
 */
import { readFileSync } from 'node:fs';

const DOMAIN = (process.argv[2] ?? '').trim();
if (!DOMAIN) {
  console.error('usage: node scripts/agents/list-planned.mjs <public|system|admin|research>');
  process.exit(2);
}

const CATALOG = 'apps/web/src/lib/domains/page-catalog.ts';
const text = readFileSync(CATALOG, 'utf8');

const entries = [];
for (const block of text.split(/\{\s*id:\s*/).slice(1)) {
  const domain = /domain:\s*'([^']+)'/.exec(block)?.[1];
  const status = /status:\s*'([^']+)'/.exec(block)?.[1];
  const path = /path:\s*'([^']+)'/.exec(block)?.[1];
  const endpoint = /endpoint:\s*(null|'[^']*')/.exec(block)?.[1] ?? 'null';
  if (domain && status && path) entries.push({ domain, status, path, endpoint });
}

const mine = entries
  .filter((e) => e.domain === DOMAIN && e.status === 'planned')
  .sort((a, b) => a.path.localeCompare(b.path));

for (const e of mine) {
  console.log(`${e.path}\t${e.endpoint === 'null' ? 'NO-ENDPOINT' : 'has-endpoint'}`);
}
console.error(`# ${DOMAIN}: ${mine.length} planned entries`);
