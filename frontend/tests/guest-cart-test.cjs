const { chromium } = require('@playwright/test');
const path = require('path');
const OUT = path.resolve(__dirname, '..', '..', 'reports', 'browser-test-2026-09-15');

(async () => {
  const b = await chromium.launch({ channel: 'chrome', headless: true });
  const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
  let cartStatus = null;
  p.on('response', (r) => { if (r.url().includes('/api/v1/marketplace/cart')) cartStatus = r.status(); });

  // fresh product id
  const ctx = await p.request.get('http://127.0.0.1:8000/api/v1/marketplace/products?limit=1');
  const pid = (await ctx.json()).products[0].id;

  await p.goto('http://localhost:5174/marketplace/products/' + pid, { waitUntil: 'networkidle', timeout: 45000 });
  await p.waitForTimeout(1200);
  const btn = p.locator('button:has-text("افزودن به سبد")').first();
  if (await btn.count()) {
    await btn.click();
    await p.waitForTimeout(1500);
  } else {
    console.log('WARN: add-to-cart button not found');
  }
  console.log(`guest POST /cart -> ${cartStatus} (200 = fixed)`);
  await p.screenshot({ path: path.join(OUT, 'product-addcart.png'), fullPage: false });

  // cart page as guest
  await p.goto('http://localhost:5174/marketplace/cart', { waitUntil: 'networkidle', timeout: 45000 });
  await p.waitForTimeout(1200);
  const body = await p.textContent('body');
  const empty = body.includes('سبد') ;
  console.log(`${empty ? 'PASS' : 'FAIL'} cart page renders for guest`);
  await p.screenshot({ path: path.join(OUT, 'cart-guest.png'), fullPage: true });

  // checkout fields parchment check
  await p.goto('http://localhost:5174/marketplace/checkout', { waitUntil: 'networkidle', timeout: 45000 });
  await p.waitForTimeout(1200);
  await p.screenshot({ path: path.join(OUT, 'checkout-parchment.png'), fullPage: true });
  const parchment = await p.evaluate(() => { const el = document.querySelector('input'); return el ? getComputedStyle(el).backgroundColor : 'none'; });
  console.log(`checkout input bg: ${parchment}`);

  await b.close();
})();
