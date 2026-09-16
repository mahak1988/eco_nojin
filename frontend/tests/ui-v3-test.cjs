const { chromium } = require('@playwright/test');
const path = require('path');
const OUT = path.resolve(__dirname, '..', '..', 'reports', 'browser-test-2026-09-15');

(async () => {
  const b = await chromium.launch({ channel: 'chrome', headless: true });
  const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
  const errs = []; p.on('pageerror', (e) => errs.push(String(e).slice(0, 150)));

  await p.goto('http://localhost:5174/marketplace/checkout', { waitUntil: 'networkidle', timeout: 45000 });
  await p.waitForTimeout(1500);
  const body = await p.textContent('body');
  const cards = ['زرینپال', 'انتقال بانکی', 'درگاه بینالمللی', 'پرداخت آزمایشی'];
  const found = cards.filter((c) => body.includes(c));
  const demoBadge = body.includes('حالت دمو');
  const escrow = body.includes('اسکرو');
  console.log(`gateways visible: ${found.length}/4 [${found.join(', ')}]`);
  console.log((demoBadge ? 'PASS' : 'FAIL') + '  demo badge on unconfigured gateways');
  console.log((escrow ? 'PASS' : 'FAIL') + '  escrow banner');
  // input bg check (no white/gray)
  const bg = await p.evaluate(() => { const el = document.querySelector('input'); return el ? getComputedStyle(el).backgroundColor : 'none'; });
  console.log(`input bg: ${bg} (must NOT be white/gray)`);
  await p.screenshot({ path: path.join(OUT, 'checkout-4gateways.png'), fullPage: true });

  // demo gateway full API flow (simulates what the UI does)
  const login = await p.request.post('http://127.0.0.1:8000/api/v1/marketplace/payments/status', { data: {} });
  console.log('status endpoint ->', login.status());
  await b.close();
})();
