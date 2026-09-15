import { FullConfig } from '@playwright/test';
import { chromium } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  const browser = await chromium.launch({ channel: 'msedge' });
  const page = await browser.newPage();
  
  await page.goto(config.projects[0].use?.baseURL || 'http://localhost:4173');
  await page.waitForLoadState('networkidle');

  const langToggle = page.getByRole('button', { name: /toggle language|تغییر زبان/i });
  if (await langToggle.isVisible()) {
    await langToggle.click();
    await page.waitForLoadState('networkidle');
  }

  await page.context().storageState({ path: 'storageState.json' });
  await browser.close();
}

export default globalSetup;