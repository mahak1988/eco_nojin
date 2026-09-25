import { expect, test } from '@playwright/test';

test('serves the baseline security headers', async ({ request }) => {
  const response = await request.get('/health');
  expect(response.status()).toBe(200);
  expect(response.headers()['x-content-type-options']).toBe('nosniff');
  expect(response.headers()['referrer-policy']).toBe('strict-origin-when-cross-origin');
  expect(response.headers()['cross-origin-opener-policy']).toBe('same-origin');
  expect(response.headers()['content-security-policy-report-only']).toContain("default-src 'self'");
  expect(response.headers()['strict-transport-security']).toContain('max-age=31536000');
});

test('rejects a BFF mutation without the CSRF intent header', async ({ request }) => {
  const response = await request.post('/api/v1/marketplace/cart', { data: {} });
  expect(response.status()).toBe(403);
});
