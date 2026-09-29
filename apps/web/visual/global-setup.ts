import { writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

/**
 * Runs once per Playwright invocation, in the driver process.
 *
 * The accessibility report is one file for one run, and the spec module is
 * evaluated once per worker — so emptying it from a `beforeAll` would leave the
 * first worker to finish holding the only findings, and the gate would pass on
 * whatever that worker happened to see. This is the one place that runs exactly
 * once.
 */
export default function globalSetup() {
  writeFileSync(resolve(import.meta.dirname, 'a11y-report.jsonl'), '');
}
