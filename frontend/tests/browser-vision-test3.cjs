const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const BASE = process.env.BASE_URL || 'http://localhost:5174';
const OUT = path.resolve(__dirname, '..', '..', 'reports', 'browser-test-2026-09-15');

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const consoleErrors = [];
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text().slice(0, 300)); });
  page.on('pageerror', (e) => consoleErrors.push('PAGEERROR: ' + String(e).slice(0, 300)));
  let failures = 0;

  // 1) category page: banner + filtered catalog
  await page.goto(BASE + '/marketplace/category/grains', { waitUntil: 'networkidle', timeout: 45000 });
  await page.waitForTimeout(1500);
  let body = await page.textContent('body');
  const catOk = body.includes('محصولات این دسته') && body.includes('غلات');
  await page.screenshot({ path: path.join(OUT, 'category-grains.png'), fullPage: true });
  console.log(`${catOk ? 'PASS' : 'FAIL'}  /marketplace/category/grains (banner+filter)`); if (!catOk) failures++;

  // 2) marketplace home: NO footer, header has بازارگاه
  await page.goto(BASE + '/marketplace', { waitUntil: 'networkidle', timeout: 45000 });
  await page.waitForTimeout(1200);
  body = await page.textContent('body');
  const footerGone = !body.includes('پشتیبانی و راهنما') && !body.includes('همکاری پژوهشی');
  const navOk = body.includes('بازارگاه');
  await page.screenshot({ path: path.join(OUT, 'marketplace-nofooter.png'), fullPage: true });
  console.log(`${footerGone ? 'PASS' : 'FAIL'}  footer removed on marketplace`);
  console.log(`${navOk ? 'PASS' : 'FAIL'}  header contains بازارگاه`);
  if (!footerGone) failures++; if (!navOk) failures++;

  // 3) product page: chart labels rendered (SVG text contains کربن/آب)
  await page.goto(BASE + '/marketplace/products/977bc924', { waitUntil: 'networkidle', timeout: 45000 });
  await page.waitForTimeout(1800);
  body = await page.textContent('body');
  const impact = body.includes('تأثیر زیستمحیطی');
  const svg = await page.evaluate(() => { const el = document.querySelector('.recharts-responsive-container svg'); return el ? el.textContent : ''; });
  const labelsIn = svg.includes('کربن') && svg.includes('آب');
  await page.screenshot({ path: path.join(OUT, 'product-chart.png'), fullPage: true });
  console.log(`${impact ? 'PASS' : 'FAIL'}  product page impact section`);
  console.log(`${labelsIn ? 'PASS' : 'FAIL'}  chart labels present (کربن/آب in svg)`);
  if (!impact) failures++; if (!labelsIn) failures++;

  fs.writeFileSync(path.join(OUT, 'console-errors-v3.log'), consoleErrors.join('\n') || '(no console errors)');
  console.log(`console errors: ${consoleErrors.length}`);
  await browser.close();
  process.exit(failures === 0 ? 0 : 1);
})();
