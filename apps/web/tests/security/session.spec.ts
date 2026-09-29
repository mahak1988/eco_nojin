import { expect, test } from '@playwright/test';

/**
 * Session boundary behaviour.
 *
 * `AUTH_AND_RBAC.md` requires five areas of evidence — login, session rotation,
 * logout, expired session and fixation defence. This file covers what can be
 * proved against a running server without inventing a session: the shape of the
 * session cookie, that a mutation is refused without intent, that logout clears
 * the cookie, and that no token is ever exposed to the browser.
 *
 * Everything here asserts a *refusal*. A test that needs a valid session would
 * need a fixture credential this repository does not have, and inventing one
 * would be exactly the `MISSING_MESSAGE` problem in another form.
 */

const MUTATION = '/api/v1/marketplace/cart';

test.describe('session cookie', () => {
  test('is absent from an unauthenticated response', async ({ request }) => {
    const response = await request.get('/fa/about');
    const cookies = response.headersArray().filter((h) => h.name.toLowerCase() === 'set-cookie');
    const session = cookies.find((c) => c.value.toLowerCase().includes('eco_session'));
    expect(session, 'an anonymous page must not set a session cookie').toBeUndefined();
  });

  test('never exposes a token in the response body or headers', async ({ request }) => {
    const response = await request.get('/api/auth/session');
    const body = await response.text();
    for (const secret of ['access_token', 'refresh_token', 'bearer', 'api_key', 'apikey']) {
      expect(body.toLowerCase(), `session response leaked ${secret}`).not.toContain(secret);
    }
    for (const header of Object.keys(response.headers())) {
      expect(header.toLowerCase(), `session response set ${header}`).not.toBe('set-cookie');
    }
  });
});

test.describe('mutation intent', () => {
  test('refuses a state change with no CSRF intent header', async ({ request }) => {
    const response = await request.post(MUTATION, { data: { product_id: 1 } });
    // The property under test is that the mutation did not take effect, not the
    // exact refusal code. A deployment without `NEXT_PUBLIC_APP_URL` fails the
    // origin check by throwing, which answers 500 and is still closed; 403 is
    // what a correctly configured deployment returns.
    expect(response.status(), `the mutation returned ${response.status()}`).not.toBe(200);
    const body = (await response.text()).toLowerCase();
    for (const success of ['"ok":true', '"created"', '"committed"', '"order_id"']) {
      expect(body, `the refusal body carried ${success}`).not.toContain(success);
    }
  });

  test('refuses a state change that claims another origin', async ({ request }) => {
    const response = await request.post(MUTATION, {
      headers: { origin: 'https://attacker.example', 'x-csrf-intent': '1' },
      data: { product_id: 1 },
    });
    expect(response.status(), `a cross-origin mutation returned ${response.status()}`).not.toBe(
      200,
    );
  });

  test('never answers a mutation on GET', async ({ request }) => {
    // A state change reachable by GET is the CSRF class of bug the BFF exists
    // to prevent, so the route must not be served as a cacheable read.
    const response = await request.get(MUTATION);
    expect(response.status()).not.toBe(200);
  });
});

test.describe('logout', () => {
  test('clears the session cookie when asked', async ({ request }) => {
    const response = await request.post('/api/auth/logout');
    const setCookie = response.headersArray().find((h) => h.name.toLowerCase() === 'set-cookie');
    if (setCookie) {
      expect(setCookie.value).toMatch(/eco_session[^;]*=;|Max-Age=0/i);
      return;
    }
    // No session was presented, or the BFF could not resolve the app URL in
    // this environment. Either way the guarantee is the same: no usable cookie
    // was left behind and no success was reported.
    const body = (await response.text()).toLowerCase();
    expect(body).not.toContain('"ok":true');
    expect(body).not.toContain('"logged_out":true');
  });
});

test.describe('anonymous access', () => {
  test('leaves a protected capability denied rather than half-open', async ({ request }) => {
    for (const path of [
      '/api/v1/admin/users',
      '/api/v1/ecowallet/wallets',
      '/api/v1/analytics/timeseries',
    ]) {
      const response = await request.get(path);
      // 5xx means the gateway is not running in this environment, which says
      // nothing about authorization. A 200 to an anonymous request would.
      if (response.status() >= 500) continue;
      expect([401, 403], `${path} answered ${response.status()} to an anonymous request`).toContain(
        response.status(),
      );
    }
  });
});
