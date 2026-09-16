const { chromium } = require('@playwright/test');
(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage();
  for (const p of ['/marketplace/disputes/new', '/marketplace/disputes']) {
    await page.goto('http://localhost:5174' + p, { waitUntil: 'networkidle', timeout: 45000 });
    await page.waitForTimeout(1000);
    const path = await page.evaluate(() => location.pathname);
    const h1 = await page.evaluate(() => Array.from(document.querySelectorAll('h1')).map((h) => h.textContent.trim()).join(' | '));
    const buttons = await page.evaluate(() => Array.from(document.querySelectorAll('button')).map((b) => b.textContent.trim()).slice(0, 5).join(' | '));
    console.log(`URL=${p} -> actual=${path} h1=[${h1}] buttons=[${buttons}]`);
  }
  await browser.close();
})();
