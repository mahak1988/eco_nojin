import { describe, expect, it } from 'vitest';
import { isAllowedOfflineMutation, isCacheablePublicRequest } from './cache-policy';

describe('offline cache policy', () => {
  it('allows public GET pages but not API or writes', () => {
    expect(isCacheablePublicRequest(new URL('https://app.test/fa/home'), 'GET', true)).toBe(true);
    expect(
      isCacheablePublicRequest(
        new URL('https://app.test/api/v1/marketplace/products'),
        'GET',
        true,
      ),
    ).toBe(false);
    expect(isCacheablePublicRequest(new URL('https://app.test/fa/home'), 'POST', true)).toBe(false);
  });

  it('only queues approved public form mutations', () => {
    expect(isAllowedOfflineMutation('/api/v1/public/education/courses', 'POST')).toBe(true);
    expect(isAllowedOfflineMutation('/api/v1/marketplace/cart', 'POST')).toBe(false);
    expect(isAllowedOfflineMutation('/api/auth/login', 'POST')).toBe(false);
  });
});
