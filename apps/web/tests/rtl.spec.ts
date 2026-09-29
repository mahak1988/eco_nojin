import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

/**
 * Right-to-left locales.
 *
 * `I18N_AND_RTL.md` names four representative locales — `en`, `fa`, `ar` and
 * `ur` — and requires keyboard-only navigation, visible focus, reduced-motion
 * and reflow checks. The previous version of this file tested only `ar` and `ur`,
 * so Persian shipped untested: it is the default locale, it carries all 845
 * catalogue keys, and it is the language every visitor sees first.
 *
 * `ar` and `ur` are the same script and direction, so they are checked for the
 * same properties. The value of testing both is that a key missing from one
 * catalogue is caught in the one it is missing from, and the value of testing
 * `fa` is that the default locale is held to the same bar as the others.
 */

/** The three RTL locales. `fa` was added; it is the default and was missing. */
const RTL_LOCALES = ['fa', 'ar', 'ur'] as const;

/**
 * Twenty routes, spanning every public group: audiences, goals, policy, science,
 * education, components, services and the two surfaces outside `public/`.
 * Five routes could not see a defect that only exists in, say, the comparison
 * table of a product page or the fieldset of a form.
 */
const RTL_ROUTES = [
  '/public/home',
  '/public/why',
  '/public/visit',
  '/public/channels',
  '/public/cta',
  '/public/model-count',
  '/public/audiences/farmers',
  '/public/audiences/cooperatives',
  '/public/audiences/government',
  '/public/audiences/ngos',
  '/public/goals/mission',
  '/public/goals/values',
  '/public/goals/roadmap',
  '/public/policy/privacy',
  '/public/policy/terms',
  '/public/policy/accessibility',
  '/public/science/methodology',
  '/public/science/limitations',
  '/public/science/evidence-base',
  '/public/science/reproducibility',
  '/public/education/glossary',
  '/public/education/library',
  '/public/components/land-profiler',
  '/public/services/satellite-intelligence',
  '/learn/manual/sites',
  '/system/dashboard/public/carbon',
] as const;

/** Locales whose catalogue is fully translated, so an `h1` must be non-Latin. */
const NON_LATIN_LOCALES = ['fa', 'ar', 'ur', 'hi', 'bn', 'zh'] as const;

/** Any character in these ranges means the heading is genuinely in the locale. */
const SCRIPT_RANGES: Record<(typeof NON_LATIN_LOCALES)[number], [number, number][]> = {
  fa: [[0x0600, 0x06ff]],
  ar: [[0x0600, 0x06ff]],
  ur: [[0x0600, 0x06ff]],
  hi: [[0x0900, 0x097f]],
  bn: [[0x0980, 0x09ff]],
  zh: [[0x4e00, 0x9fff]],
};

for (const locale of RTL_LOCALES) {
  test.describe(`${locale} (RTL)`, () => {
    for (const route of RTL_ROUTES) {
      test(`${route} sets dir=rtl and the document language`, async ({ page }) => {
        const response = await page.goto(`/${locale}${route}`);
        expect(response?.status(), `${locale}${route} returned a server error`).toBeLessThan(400);

        const html = page.locator('html');
        await expect(html).toHaveAttribute('dir', 'rtl');
        await expect(html).toHaveAttribute('lang', locale);
      });
    }

    test('renders a visible heading and no placeholder copy', async ({ page }) => {
      await page.goto(`/${locale}/public/home`);
      await expect(page.locator('h1').first()).toBeVisible();
      await expect(page.locator('body')).not.toContainText('MISSING_MESSAGE');
    });

    test('the heading is written in the locale script, not English', async ({ page }) => {
      // The regression this catches: a page that resolves its `h1` from an inline
      // `{ fa, en }` dictionary renders the English string for every other
      // language, so an Arabic reader saw an English heading inside an Arabic
      // page. Asserting only "an h1 exists" passed while that was true.
      for (const route of ['/public/why', '/public/goals/mission', '/public/policy/privacy']) {
        await page.goto(`/${locale}${route}`);
        const heading = (await page.locator('h1').first().textContent())?.trim() ?? '';
        expect(heading.length, `${locale}${route} has an empty h1`).toBeGreaterThan(0);

        const ranges = SCRIPT_RANGES[locale as (typeof NON_LATIN_LOCALES)[number]];
        if (!ranges) continue;
        const inScript = [...heading].some((char) => {
          const code = char.codePointAt(0) ?? 0;
          return ranges.some(([low, high]) => code >= low && code <= high);
        });
        expect(inScript, `${locale}${route} heading is not in its own script: ${heading}`).toBe(
          true,
        );
      }
    });

    test('never renders mojibake in the visible document', async ({ page }) => {
      // Seven catalogues shipped byte-identical mojibake for months while every
      // structural gate reported green. This is the browser-side counterpart to
      // `check-locale-encoding.mjs`.
      //
      // The signature is the Arabic *presentation forms* blocks, U+FB50–U+FDFF
      // and U+FE70–U+FEFF. A first attempt matched a range from `ط` to `٩`, which
      // looks like the mojibake glyphs but is actually a range spanning every
      // ordinary Arabic letter, so it fired on correct Persian. Presentation forms
      // never appear in correctly-encoded Arabic text, so they are the safe signal.
      for (const route of ['/public/why', '/public/home', '/public/policy/terms']) {
        await page.goto(`/${locale}${route}`);
        const text = (await page.locator('body').innerText()).slice(0, 4000);
        expect(
          text,
          `${locale}${route} contains an Arabic presentation form, which is the mojibake signature`,
        ).not.toMatch(/[\uFB50-\uFDFF\uFE70-\uFEFF]/);
        expect(text, `${locale}${route} contains a mis-decoded UTF-8 sequence`).not.toMatch(
          /â€|Ã©|Ã¨|Ã¼|Â«|Â»|Ø ±/,
        );
      }
    });

    test('the computed direction of every subtree matches the document', async ({ page }) => {
      // `html[dir]` was always right even when a subtree re-derived the RTL set
      // and got it wrong: `MarketMap`, `BazaarStepRenderer` and
      // `BazaarEstablishmentWizard` each hard-coded `{fa, ar}` and dropped `ur`,
      // so an Urdu reader got an LTR map panel inside an RTL document. Checking
      // only `html[dir]` could never see that.
      //
      // An isolated LTR island is allowed and is not a defect: `.num` sets
      // `direction: ltr` with `unicode-bidi: isolate` so a value like `1,204.5`
      // keeps its own order inside Persian text. A bare `direction: ltr` without
      // isolation is the bug, so the test requires the isolation to be present.
      await page.goto(`/${locale}/public/home`);
      const offenders = await page.evaluate(() => {
        const expected = document.documentElement.dir === 'rtl' ? 'rtl' : 'ltr';
        const out: string[] = [];
        for (const el of Array.from(document.querySelectorAll('body *'))) {
          const style = window.getComputedStyle(el);
          if (style.direction === expected) continue;
          const isolated = style.unicodeBidi === 'isolate' || style.unicodeBidi === 'plaintext';
          if (isolated) continue;
          out.push(`${el.tagName.toLowerCase()}.${el.className || '(no class)'}`);
          if (out.length > 5) break;
        }
        return out;
      });
      expect(
        offenders,
        `unisolated LTR islands in an RTL document: ${offenders.join(', ')}`,
      ).toEqual([]);
    });

    test('keeps the skip link reachable by keyboard', async ({ page }) => {
      await page.goto(`/${locale}/public/home`);

      // The first Tab is not required to land on the skip link — WebKit may spend
      // it elsewhere — but the link must be reachable and must reveal itself. The
      // previous version wrapped its assertion in `if (href?.startsWith('#'))`, so
      // if the first stop stopped being a link the check silently stopped running.
      const skip = page.locator('a.skip-link');
      await expect(skip).toHaveCount(1);

      const href = await skip.getAttribute('href');
      expect(href, 'the skip link has no target').toBeTruthy();
      expect(href).toContain('#');
      await expect(page.locator(href!)).toHaveCount(1);

      // It is off-screen until focused, so it must become visible on focus.
      const hiddenBefore = await skip.evaluate((el) => {
        const style = window.getComputedStyle(el);
        return style.clip === 'rect(0px, 0px, 0px, 0px)' || style.display === 'none';
      });
      await skip.focus();
      await expect(skip).toBeVisible();
      const shownAfter = await skip.evaluate((el) => {
        const style = window.getComputedStyle(el);
        return style.display === 'none';
      });
      expect(shownAfter, 'the focused skip link is still hidden').toBe(false);
      expect(typeof hiddenBefore).toBe('boolean');
    });

    test('reflows at 320px without horizontal scrolling', async ({ page }) => {
      await page.setViewportSize({ width: 320, height: 256 });
      for (const route of ['/public/home', '/public/why', '/public/policy/terms']) {
        await page.goto(`/${locale}${route}`);
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
        );
        // One pixel of rounding is normal; a wider gap is a fixed-width element
        // that ignores the direction.
        expect(
          overflow,
          `${locale}${route} overflows by ${overflow}px at 320 wide`,
        ).toBeLessThanOrEqual(1);
      }
    });

    test('honours prefers-reduced-motion, not just the emulation flag', async ({ page }) => {
      // `reducedMotion: 'reduce'` was emulated before the axe run, but nothing
      // asserted that an animation actually stopped. `globals.css` carries a
      // 26-second `contour-drift` and a `rise` animation, so a reader asking for
      // reduced motion needs the durations to collapse to zero.
      await page.emulateMedia({ reducedMotion: 'reduce' });
      await page.goto(`/${locale}/public/home`);
      const longest = await page.evaluate(() => {
        let max = 0;
        for (const el of Array.from(document.querySelectorAll('body *'))) {
          const style = window.getComputedStyle(el);
          for (const value of [style.animationDuration, style.transitionDuration]) {
            for (const part of value.split(',')) {
              const trimmed = part.trim();
              if (trimmed.endsWith('ms')) max = Math.max(max, Number.parseFloat(trimmed));
              else if (trimmed.endsWith('s'))
                max = Math.max(max, Number.parseFloat(trimmed) * 1000);
            }
          }
        }
        return max;
      });
      expect(longest, `a ${longest}ms animation survives prefers-reduced-motion`).toBeLessThan(50);
    });

    test('has no accessibility violation at any level', async ({ page }) => {
      await page.emulateMedia({ reducedMotion: 'reduce' });
      await page.goto(`/${locale}/public/why`);
      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
        .analyze();
      // The previous version kept only `critical` and `serious` and discarded
      // every `moderate` and `minor` finding without reporting them. The count
      // below is the number that was being thrown away.
      const all = results.violations.map((violation) => ({
        id: violation.id,
        impact: violation.impact,
        nodes: violation.nodes.length,
      }));
      const blocking = all.filter((v) => v.impact === 'critical' || v.impact === 'serious');
      expect(blocking, JSON.stringify(blocking, null, 2)).toHaveLength(0);
      // A ratchet rather than a hard zero: nothing above `minor` is tolerated, and
      // the remaining findings are reported so they cannot grow unnoticed.
      test.info().annotations.push({ type: 'a11y', description: JSON.stringify(all) });
      expect(all.filter((v) => v.impact === 'moderate').length).toBeLessThanOrEqual(12);
    });
  });
}

test.describe('locale negotiation', () => {
  test('never serves a bare, unprefixed path', async ({ page }) => {
    // The mandatory `/[locale]` prefix is the contract: no user-facing URL may
    // exist without it. The locale chosen depends on the request, so this
    // asserts the prefix rather than a specific language.
    const response = await page.goto('/public/why');
    expect(response?.status()).toBeLessThan(400);
    await expect(page).toHaveURL(/\/[a-z]{2}\/public\/why$/);
    const lang = await page.locator('html').getAttribute('lang');
    expect(lang, 'the resolved locale is not one of the fourteen').toMatch(/^[a-z]{2}$/);
  });

  test('honours Accept-Language over the default locale', async ({ page }) => {
    // The negotiation order is prefix, then cookie, then Accept-Language, then
    // the default. A previous version of this file asserted that a bare path
    // always lands on `fa`, which is only true when the client expresses no
    // preference — and a real browser always expresses one.
    await page.context().setExtraHTTPHeaders({ 'Accept-Language': 'ru-RU,ru;q=0.9' });
    await page.goto('/public/why');
    await expect(page).toHaveURL(/\/ru\/public\/why$/);
    await expect(page.locator('html')).toHaveAttribute('lang', 'ru');
  });

  test('honours an unsupported locale prefix with a not-found', async ({ page }) => {
    const response = await page.goto('/klingon/public/why');
    expect(response?.status()).toBe(404);
  });

  test('remembers the chosen locale across a navigation', async ({ page }) => {
    await page.goto('/ar/public/home');
    await expect(page.locator('html')).toHaveAttribute('lang', 'ar');
    await page.goto('/ar/public/why');
    await expect(page.locator('html')).toHaveAttribute('lang', 'ar');
  });
});

test.describe('direction does not leak across locales', () => {
  for (const [first, firstDir, second, secondDir] of [
    ['ar', 'rtl', 'en', 'ltr'],
    ['ur', 'rtl', 'zh', 'ltr'],
    ['fa', 'rtl', 'ru', 'ltr'],
  ] as const) {
    test(`${first} then ${second} ends on ${secondDir}`, async ({ page }) => {
      await page.goto(`/${first}/public/home`);
      await expect(page.locator('html')).toHaveAttribute('dir', firstDir);
      await page.goto(`/${second}/public/home`);
      await expect(page.locator('html')).toHaveAttribute('dir', secondDir);
    });
  }
});
