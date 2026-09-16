const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const BASE = process.env.BASE_URL || 'http://localhost:5174';
const OUT = path.resolve(__dirname, '..', '..', 'reports', 'browser-test-2026-09-15');

const PAGES = [
  { url: '/marketplace/checkout', file: 'checkout-gateways.png', expect: ['انتخاب درگاه پرداخت', 'اسکرو', 'زرینپال'] },
  { url: '/marketplace/apply', file: 'vendor-agreement.png', expect: ['دستورالعمل و قرارداد فروشندگی', 'تایید میکنم'] },
  { url: '/marketplace/create', file: 'marketplace-covenant.png', expect: ['منشور و قرارداد تشکیل بازارچه', 'پالت رنگ سازمانی'] },
];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const consoleErrors = [];
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text().slice(0, 300)); });
  page.on('pageerror', (e) => consoleErrors.push('PAGEERROR: ' + String(e).slice(0, 300)));

  let failures = 0;
  for (const spec of PAGES) {
    try {
      await page.goto(BASE + spec.url, { waitUntil: 'networkidle', timeout: 45000 });
      await page.waitForTimeout(1500);
      const body = await page.textContent('body');
      const found = spec.expect.filter((t) => body.includes(t));
      await page.screenshot({ path: path.join(OUT, spec.file), fullPage: true });
      const ok = found.length === spec.expect.length;
      if (!ok) failures++;
      console.log(`${ok ? 'PASS' : 'FAIL'}  ${spec.url}  hits=[${found.join(', ')}]  shot=${spec.file}`);
    } catch (err) {
      failures++;
      console.log(`FAIL  ${spec.url}  ERROR: ${String(err).slice(0, 200)}`);
    }
  }
  fs.writeFileSync(path.join(OUT, 'console-errors-v2.log'), consoleErrors.join('\n') || '(no console errors)');
  console.log(`console errors: ${consoleErrors.length}`);
  await browser.close();
  process.exit(failures === 0 ? 0 : 1);
})();
