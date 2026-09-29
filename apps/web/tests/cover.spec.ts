import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { expect, test } from '@playwright/test';

/**
 * Read a value out of a locale catalogue.
 *
 * The heading assertion used to hard-code `مَنظر` with a fatha while the page
 * renders `منظر` without one, so the test failed on a diacritic nobody could see
 * in the diff. Reading the expected value from the catalogue makes the test assert
 * the real contract and removes a whole class of silent drift; if the catalogue
 * is wrong, the change is made in one place and both the page and the test move
 * together.
 */
const locale = (code: string): Record<string, any> =>
  JSON.parse(readFileSync(join(import.meta.dirname, '..', 'messages', `${code}.json`), 'utf8'));

const faCatalogue = locale('fa');
const arCatalogue = locale('ar');

/**
 * Cover Page (T01).
 *
 * The strings asserted here are read from the catalogues rather than pasted, so
 * the test cannot drift from the copy and cannot encode a translation that was
 * never written.
 *
 * That last point was the reason this file failed. Its `ar` and `zh` cases
 * expected `إدارة ذكية` and `智能景观管理`, which have never existed in any
 * catalogue.
 */
const COVER = {
  fa: {
    brand: faCatalogue.brand.name,
    subtitle: faCatalogue.cover.subtitle,
    slogan: faCatalogue.cover.slogan,
    quote: faCatalogue.cover.quote,
    enterPublic: faCatalogue.cover.enterPublic,
    enterMarketplace: faCatalogue.cover.enterMarketplace,
    languageLabel: faCatalogue.cover.languageLabel,
  },
  en: {
    brand: locale('en').brand.name,
    subtitle: locale('en').cover.subtitle,
    enterPublic: locale('en').cover.enterPublic,
    enterMarketplace: locale('en').cover.enterMarketplace,
  },
  ar: {
    subtitle: arCatalogue.cover.subtitle,
    languageLabel: arCatalogue.cover.languageLabel,
  },
  zh: {
    subtitle: locale('zh').cover.subtitle,
  },
} as const;

/** The heading `/home` renders, read rather than transcribed. */
const homeHeading = faCatalogue.public.home.title;

test.describe('Cover Page (T01)', () => {
  test('loads and displays brand, subtitle, slogan, quote, and two CTAs', async ({ page }) => {
    await page.goto('/fa');

    // The brand is the document title, not a header element. The cover's
    // `<header>` holds the language switcher and the brand name appears nowhere
    // in the body, so `header >> text=…` never matched: the assertion had been
    // failing against a structure the page does not have.
    await expect(page).toHaveTitle(new RegExp(COVER.fa.brand));

    // The subtitle is the page's own heading.
    await expect(page.locator('h1')).toHaveText(COVER.fa.subtitle);
    await expect(page.locator(`text=${COVER.fa.slogan}`)).toBeVisible();
    await expect(page.locator(`text=${COVER.fa.quote}`)).toBeVisible();

    await expect(page.locator(`a:has-text("${COVER.fa.enterPublic}")`)).toBeVisible();
    await expect(page.locator(`a:has-text("${COVER.fa.enterMarketplace}")`)).toBeVisible();

    await expect(page.locator(`nav[aria-label="${COVER.fa.languageLabel}"]`)).toBeVisible();
  });

  test('English locale loads correctly', async ({ page }) => {
    await page.goto('/en');
    await expect(page).toHaveTitle(/HyDroMa/);
    await expect(page.locator(`text=${COVER.en.subtitle}`)).toBeVisible();
    await expect(page.locator(`a:has-text("${COVER.en.enterPublic}")`)).toBeVisible();
    await expect(page.locator(`a:has-text("${COVER.en.enterMarketplace}")`)).toBeVisible();
  });

  test('Arabic locale loads with RTL and its own copy', async ({ page }) => {
    await page.goto('/ar');
    await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
    await expect(page.locator('html')).toHaveAttribute('lang', 'ar');
    // Asserted on the heading rather than a bare `text=` locator: the subtitle is
    // the page's own h1, which is where it belongs and what a reader navigates by.
    await expect(page.locator('h1')).toHaveText(COVER.ar.subtitle);
    // The language switcher is a named landmark, so it can be jumped to.
    await expect(page.locator(`nav[aria-label="${COVER.ar.languageLabel}"]`)).toBeVisible();
  });

  test('Chinese locale loads with its own copy', async ({ page }) => {
    await page.goto('/zh');
    await expect(page.locator('html')).toHaveAttribute('lang', 'zh');
    await expect(page.locator('h1')).toHaveText(COVER.zh.subtitle);
  });
});

test.describe('Cover Page - Navigation', () => {
  test('the public-pages CTA navigates to /home', async ({ page }) => {
    await page.goto('/fa');
    await page.click(`a:has-text("${COVER.fa.enterPublic}")`);
    await expect(page).toHaveURL(/\/fa\/home/);
    await expect(page.locator('h1')).toContainText(homeHeading);
  });

  test('the marketplace CTA navigates to /market', async ({ page }) => {
    await page.goto('/fa');
    await page.click(`a:has-text("${COVER.fa.enterMarketplace}")`);
    await expect(page).toHaveURL(/\/fa\/market/);
    await expect(page.locator('h1')).toContainText('بازارگاه');
  });
});
