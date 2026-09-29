// Diagnostic probe: why does the cover CTA click not navigate?
// Run: node .openclaw/tmp/cta-probe.mjs http://127.0.0.1:3111
import { chromium } from '@playwright/test';

const base = process.argv[2] ?? 'http://127.0.0.1:3111';
const browser = await chromium.launch({ channel: 'msedge' });
const page = await browser.newPage();

const logs = [];
page.on('console', (m) => logs.push(`[console:${m.type()}] ${m.text()}`));
page.on('pageerror', (e) => logs.push(`[pageerror] ${e.message}`));
page.on('requestfailed', (r) =>
  logs.push(`[requestfailed] ${r.url()} :: ${r.failure()?.errorText}`),
);

await page.goto(`${base}/fa`, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(1500);

const before = page.url();
const href = await page.getAttribute('a:has-text("ورود به صفحات عمومی")', 'href');
console.log('url before click :', before);
console.log('anchor href      :', href);

await page.click('a:has-text("ورود به صفحات عمومی")');
await page.waitForTimeout(4000);
console.log('url after click  :', page.url());

// Try direct client navigation via history to see whether the router works at all
await page.goto(`${base}/fa/home`, { waitUntil: 'domcontentloaded' });
console.log('direct goto home :', page.url());

console.log('\n--- captured events ---');
for (const line of logs.slice(0, 40)) console.log(line);
console.log('total captured:', logs.length);

await browser.close();
