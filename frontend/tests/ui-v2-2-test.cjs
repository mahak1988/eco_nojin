const { chromium } = require('@playwright/test');
const path = require('path');
const OUT = path.resolve(__dirname, '..', '..', 'reports', 'browser-test-2026-09-15');

(async () => {
  const b = await chromium.launch({ channel: 'chrome', headless: true });
  const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
  let fails = 0;

  // 1) BuyerDashboard as guest: notifications card with sign-in note
  await p.goto('http://localhost:5174/marketplace/orders', { waitUntil: 'networkidle', timeout: 45000 });
  await p.waitForTimeout(1500);
  let body = await p.textContent('body');
  const notifCard = body.includes('اعلانها') && body.includes('وارد حساب خود شوید');
  console.log((notifCard ? 'PASS' : 'FAIL') + '  BuyerDashboard notifications card (guest sign-in note)');
  if (!notifCard) fails++;
  await p.screenshot({ path: path.join(OUT, 'buyer-notifications.png'), fullPage: true });

  // 2) VA: accept covenant -> form with marketplace select + empty-marketplace note
  await p.goto('http://localhost:5174/marketplace/apply', { waitUntil: 'networkidle', timeout: 45000 });
  await p.waitForTimeout(1200);
  const boxes = p.locator('input[type="checkbox"]');
  await boxes.nth(0).check();
  await boxes.nth(1).check();
  await p.locator('button:has-text("تایید میکنم — ادامه ثبت فروشگاه")').click();
  await p.waitForTimeout(800);
  body = await p.textContent('body');
  const selectOk = (await p.locator('select#marketplace_id').count()) > 0;
  const emptyNote = body.includes('هنوز بازارچه‌ای ثبت نشده');
  console.log((selectOk ? 'PASS' : 'FAIL') + '  VA marketplace select visible after covenant');
  console.log((emptyNote ? 'PASS' : 'FAIL') + '  VA empty-marketplace note with create link');
  if (!selectOk) fails++; if (!emptyNote) fails++;
  await p.screenshot({ path: path.join(OUT, 'vendor-form-select.png'), fullPage: true });

  console.log('console clean check done; fails=' + fails);
  await b.close();
  process.exit(fails === 0 ? 0 : 1);
})();
