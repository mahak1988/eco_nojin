import { readdir, readFile } from 'node:fs/promises';
import { join, relative } from 'node:path';

const root = join(process.cwd(), 'apps/web/src/app');
const offenders = [];

async function walk(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      await walk(path);
      continue;
    }
    if (!entry.name.endsWith('page.tsx')) continue;
    const content = await readFile(path, 'utf8');
    if (content.includes('verified={true}') || /verified:\s*true/.test(content)) {
      offenders.push(relative(process.cwd(), path));
    }
  }
}

await walk(root);
if (offenders.length > 0) {
  console.error(`Unverified provenance claims found in ${offenders.length} pages:`);
  for (const offender of offenders) console.error(`- ${offender}`);
  process.exit(1);
}
console.log('All page provenance claims are explicitly unverified or sourced.');
