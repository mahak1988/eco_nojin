#!/usr/bin/env node
/**
 * Core Web Vitals budget gate.
 *
 * `TESTING.md` requires "Lighthouse/CWV checks" as gate 8, and no such command
 * existed in the repository. This runs the budget in
 * `apps/web/lighthouserc.json` against a running production server.
 *
 * Two things are checked and reported separately, because they mean different
 * things:
 *
 *   - **Lab budgets** are measured here and are a release gate.
 *   - **INP is a field metric.** `TESTING.md` already says so, and this script
 *     does not pretend a lab run measures it. The collection endpoint exists at
 *     `app/api/observability/web-vitals`; turning that stream into a field budget
 *     needs real user data and is listed in the status report as open.
 *
 * The gate needs a production server and the `lighthouse` CLI. When either is
 * missing it says so and exits non-zero, because a check that silently passes
 * when it cannot run is worse than no check.
 */
import { spawnSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const WEB_ROOT = join(REPO_ROOT, 'apps', 'web');
const CONFIG = join(WEB_ROOT, 'lighthouserc.json');
const BASE_URL = process.env.CWV_BASE_URL ?? 'http://localhost:3001';

function fail(message) {
  console.error(`CWV gate cannot run:\n  ${message}\n`);
  process.exit(1);
}

const probe = spawnSync('node', ['-e', `fetch('${BASE_URL}/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))`], {
  stdio: 'ignore',
});
if (probe.status !== 0) {
  fail(
    `no server answering at ${BASE_URL}. Start one with \`pnpm -C apps/web build && pnpm -C apps/web start\`, ` +
      'or point CWV_BASE_URL at a running instance.',
  );
}

const lighthouse = spawnSync('npx', ['--no-install', 'lighthouse', '--config-path', CONFIG], {
  cwd: WEB_ROOT,
  stdio: 'inherit',
});

if (lighthouse.error || lighthouse.status !== 0) {
  fail(
    'the `lighthouse` CLI is not installed. Add it as a devDependency; the budget in ' +
      'apps/web/lighthouserc.json is ready and will be enforced once it is.',
  );
}

console.log(`CWV budgets met for ${BASE_URL}. INP remains a field metric and is not asserted here.`);
