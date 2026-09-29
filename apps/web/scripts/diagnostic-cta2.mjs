// Deeper diagnostic: is the click's default prevented, and by what?
import { chromium } from '@playwright/test';

const base = process.argv[2] ?? 'http://127.0.0.1:3111';
const browser = await chromium.launch({ channel: 'msedge' });
const page = await browser.newPage();

const errors = [];
page.on('pageerror', (e) => errors.push(`[pageerror] ${e.message}`));
page.on('requestfailed', (r) => errors.push(`[requestfailed] ${r.url()} :: ${r.failure()?.errorText}`));
page.on('framenavigated', (f) => {
  if (f === page.mainFrame()) errors.push(`[framenavigated] ${f.url()}`);
});

await page.addInitScript(() => {
  window.__clicks = [];
  window.addEventListener(
    'click',
    (e) => {
      const t = e.target;
      window.__clicks.push({
        tag: t?.tagName ?? '?',
        href: t?.closest?.('a')?.getAttribute('href') ?? null,
        defaultPrevented: e.defaultPrevented,
        phase: 'bubble-window',
      });
    },
    false,
  );
});

await page.goto(`${base}/fa`, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(2000);

const env = await page.evaluate(() => ({
  onLine: navigator.onLine,
  swController: navigator.serviceWorker?.controller?.scriptURL ?? null,
  swRegistrations: undefined,
}));
console.log('environment :', JSON.stringify(env));

await page.click('a:has-text("ورود به صفحات عمومی")');
await page.waitForTimeout(3500);

const after = await page.evaluate(() => ({
  url: location.href,
  clicks: window.__clicks,
}));
console.log('url after   :', after.url);
console.log('clicks      :', JSON.stringify(after.clicks, null, 2));

console.log('\n--- browser events ---');
for (const line of errors.slice(0, 20)) console.log(line);
console.log('total events:', errors.length);

await browser.close();
