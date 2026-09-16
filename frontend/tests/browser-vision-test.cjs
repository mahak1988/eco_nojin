/**
 * Browser vision test — Bazargah plan-v2.0 pages on the running dev stack.
 * Uses the locally installed Chrome (channel: "chrome"), headless.
 * Screenshots + console logs land in reports/browser-test-2026-09-15/.
 */
const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const BASE = process.env.BASE_URL || 'http://localhost:5174';
const OUT = path.resolve(__dirname, '..', 'reports', 'browser-test-2026-09-15');

const PAGES = [
  { url: '/marketplace', file: 'catalog.png', expect: ['بازارگاه', 'Market'] },
  { url: '/marketplace/disputes/new', file: 'dispute-form.png', expect: ['ثبت شکایت'] },
  { url: '/marketplace/disputes', file: 'disputes-list.png', expect: ['شکایات'] },
];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const consoleErrors = [];
  page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text().slice(0, 300)); });
  page.on('pageerror', (err) => consoleErrors.push('PAGEERROR: ' + String(err).slice(0, 300)));

  let failures = 0;
  for (const spec of PAGES) {
    const url = BASE + spec.url;
    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 45000 });
      await page.waitForTimeout(1500);
      const body = await page.textContent('body');
      const found = spec.expect.filter((t) => body.includes(t));
      const shot = path.join(OUT, spec.file);
      await page.screenshot({ path: shot, fullPage: true });
      const ok = found.length > 0;
      if (!ok) failures++;
      console.log(`${ok ? 'PASS' : 'FAIL'}  ${url}  expected-hit=[${found.join(', ')}]  shot=${spec.file}`);
    } catch (err) {
      failures++;
      console.log(`FAIL  ${url}  ERROR: ${String(err).slice(0, 200)}`);
    }
  }

  fs.writeFileSync(path.join(OUT, 'console-errors.log'), consoleErrors.join('\n') || '(no console errors)');
  console.log(`console errors: ${consoleErrors.length} (saved to console-errors.log)`);
  await browser.close();
  process.exit(failures === 0 ? 0 : 1);
})();
