/**
 * How many "successes" are not successes?
 *
 * The project rule is "real data or an explicit label", and §7 of the master plan
 * requires a model version, a calibration, a confidence interval and a run
 * identifier on every scientific output. A stub that returns `status: "success"`
 * for an operation that was never implemented violates that rule in the most
 * expensive way possible: a client that checks `status` cannot tell the
 * difference between a real run and a fabrication, and a `latency_ms` measured
 * around a function that did nothing is a real number describing a fake
 * operation.
 *
 * This does not try to prove intent. It reports every place where a success
 * status sits next to an admission that nothing ran, and every unrecognised
 * token that looks like a stub, so a human decides.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO = join(dirname(dirname(fileURLToPath(import.meta.url))));
const SERVICES = process.argv[2] ?? join(REPO, 'services');

function walk(dir, acc = []) {
  for (const name of readdirSync(dir)) {
    if (name === '__pycache__') continue;
    const full = join(dir, name);
    if (statSync(full).isDirectory()) walk(full, acc);
    else if (name.endsWith('.py')) acc.push(full);
  }
  return acc;
}

/** Phrases that admit the operation did not happen. */
const ADMISSION =
  /not yet implemented|not implemented|mock|placeholder|stub|hardcoded|hard-coded|dummy|TODO|FIXME|sample data|for now, return|In a real implementation/i;

/**
 * Phrases that claim the operation did happen.
 *
 * `status: "success"` is the obvious one and not the only one. Two shapes found
 * in this repository are worse and were missed by the obvious pattern:
 *
 *   - a validation endpoint that reports `passed: 6, failed: 0` from a fixture
 *     file rather than from running anything (`hydroma_dashboard.py:763`);
 *   - a response that carries a fabricated metric beside a `# Mock` comment
 *     (`admin_overview.py:106`).
 *
 * The admission is usually in a comment — that is the normal case, a developer
 * documenting their own stub. The *claim* must not be. `auth_supabase.py`
 * documents an opt-in offline fallback honestly across six comments, and flagging
 * those would train a reader to ignore this gate, so the claim is tested against
 * the line with its trailing comment removed.
 */
const CLAIM =
  /(?:^|[^\w])(?:["']status["']\s*:\s*["']success["']|status\s*=\s*["']success["']|["']?(?:passed|pass_rate)["']?\s*[:=]\s*\d)/;

/** The part of a line that is not a trailing `#` comment. */
const code = (line) => {
  const hash = line.indexOf('#');
  return hash === -1 ? line : line.slice(0, hash);
};

const findings = [];
const admissions = [];

for (const file of walk(SERVICES)) {
  const source = readFileSync(file, 'utf8');
  const lines = source.split('\n');

  lines.forEach((line, i) => {
    if (!ADMISSION.test(line)) return;
    const window = lines
      .slice(Math.max(0, i - 6), Math.min(lines.length, i + 12))
      .map(code)
      .join('\n');
    const entry = {
      file: relative(REPO, file).replace(/\\/g, '/'),
      line: i + 1,
      text: line.trim().slice(0, 92),
      claimsSuccess: CLAIM.test(window),
    };
    if (entry.claimsSuccess) findings.push(entry);
    else admissions.push(entry);
  });
}

console.log(`scanned ${walk(SERVICES).length} python files under services/`);
console.log(`lines admitting the operation did not happen: ${admissions.length + findings.length}`);
console.log(`  …of which ALSO report a success nearby        : ${findings.length}`);
console.log(`  …with no success claim nearby                 : ${admissions.length}`);

if (findings.length) {
  console.log(`\n=== FABRICATED SUCCESS: a stub that reports success ===`);
  for (const f of findings) {
    console.log(`  ${f.file}:${f.line}`);
    console.log(`      ${f.text}`);
  }
}

console.log(`\n=== admitted stubs, no success claim (lower severity) ===`);
for (const a of admissions) {
  console.log(`  ${a.file}:${a.line}  ${a.text}`);
}

process.exit(findings.length > 0 ? 1 : 0);
