import { NextRequest } from 'next/server';
import { describe, expect, it } from 'vitest';
import { assertBffRequest, BffError } from './backend';

describe('assertBffRequest', () => {
  it('allows safe same-origin reads without an Origin header', () => {
    expect(() =>
      assertBffRequest(new NextRequest('http://localhost:3001/api/v1/platform/health')),
    ).not.toThrow();
  });

  it('rejects mutations without the CSRF intent header', () => {
    const request = new NextRequest('http://localhost:3001/api/v1/marketplace/cart', {
      method: 'POST',
      headers: { origin: 'http://localhost:3001' },
    });
    expect(() => assertBffRequest(request)).toThrow(BffError);
  });

  it('rejects a cross-site mutation', () => {
    const request = new NextRequest('http://localhost:3001/api/v1/marketplace/cart', {
      method: 'POST',
      headers: {
        origin: 'http://localhost:3001',
        'x-csrf-intent': '1',
        'sec-fetch-site': 'cross-site',
      },
    });
    expect(() => assertBffRequest(request)).toThrow(BffError);
  });

  it('accepts a same-origin mutation with CSRF intent', () => {
    const request = new NextRequest('http://localhost:3001/api/v1/marketplace/cart', {
      method: 'POST',
      headers: {
        origin: 'http://localhost:3001',
        'x-csrf-intent': '1',
      },
    });
    expect(() => assertBffRequest(request)).not.toThrow();
  });
});
