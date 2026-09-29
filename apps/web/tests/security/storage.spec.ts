import { expect, test } from '@playwright/test';

/**
 * Nothing secret may reach the browser.
 *
 * `AUTH_AND_RBAC.md` prohibits bearer tokens in `localStorage` or
 * `sessionStorage`, a browser-supplied `Authorization` header as the normal
 * authentication path, and any secret appearing in browser storage, HTML, logs
 * or analytics events. A unit test can read the policy module; only a running
 * page can prove what actually ends up in storage, so both are checked here.
 */

const STORAGE_KEYS = ['token', 'access_token', 'refresh_token', 'id_token', 'apiKey', 'api_key'];

test.describe('browser storage', () => {
  for (const route of ['/fa/home', '/fa/public/why', '/fa/learn/manual/sites']) {
    test(`${route} writes no credential into web storage`, async ({ page }) => {
      await page.goto(route);
      const leaked = await page.evaluate((keys) => {
        const found: string[] = [];
        for (const store of [window.localStorage, window.sessionStorage]) {
          for (let i = 0; i < store.length; i += 1) {
            const name = store.key(i) ?? '';
            if (keys.some((key) => name.toLowerCase().includes(key))) found.push(name);
          }
        }
        return found;
      }, STORAGE_KEYS);

      expect(leaked, `${route} put ${leaked.join(', ')} into web storage`).toEqual([]);
    });
  }

  test('emits no token into the served HTML', async ({ request }) => {
    const html = await (await request.get('/fa/home')).text();
    // A JWT is three base64url segments; the pattern is narrow on purpose so a
    // stray long base64 string does not fail the build.
    expect(html).not.toMatch(/\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/);
    expect(html.toLowerCase()).not.toContain('bearer ');
  });
});

test.describe('authentication path', () => {
  test('reaches the gateway through the same-origin BFF, not a browser header', async ({
    page,
  }) => {
    const headers: string[] = [];
    page.on('request', (request) => {
      if (!request.url().includes('/api/')) return;
      // Playwright reports absent headers as empty strings, so only a value that
      // is actually present counts as a browser-supplied credential.
      const value = request.headers()['authorization'];
      if (value) headers.push(value);
    });
    await page.goto('/fa/learn/manual/sites');
    await page.waitForLoadState('networkidle').catch(() => undefined);

    expect(headers, `the browser sent an Authorization header: ${headers.join(', ')}`).toEqual([]);
  });

  test('keeps the session cookie off client-readable script', async ({ request }) => {
    const html = await (await request.get('/fa/home')).text();
    // The session is a cookie; the markup must not also carry its value.
    const inlineCookie = /eco_session[^\n]{0,40}=[A-Za-z0-9_-]{8,}/.exec(html);
    expect(inlineCookie, 'a session value appears in the HTML').toBeNull();
  });
});
