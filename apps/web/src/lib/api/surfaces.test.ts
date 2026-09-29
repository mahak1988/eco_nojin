import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { setApiBaseUrl } from './client';
import {
  CONTENT_SEARCH_SOURCE,
  contentSearchSource,
  DASHBOARD_PUBLIC_SOURCES,
  dashboardPublicSource,
  getDashboardPublic,
  MARKETPLACE_PRODUCERS_SOURCE,
  MARKETPLACE_STATS_SOURCE,
  searchContent,
  verificationOf,
} from './surfaces';

const ORIGIN = 'https://api.example.test';
const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  setApiBaseUrl(ORIGIN);
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
  setApiBaseUrl('/api');
});

function jsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: 'status',
    text: async () => JSON.stringify(body),
  } as unknown as Response;
}

function requestedUrl(call = 0): string {
  return String(fetchMock.mock.calls[call]?.[0] ?? '');
}

describe('surface sources', () => {
  it('uses the router prefix the gateway actually mounts', () => {
    // The public dashboard router is mounted at the application root, not under
    // `/api/v1`; a wrong prefix would silently 404 on every dashboard surface.
    expect(DASHBOARD_PUBLIC_SOURCES.full).toBe('/dashboard/public/full');
    expect(dashboardPublicSource('carbon')).toBe('/dashboard/public/carbon');
    expect(MARKETPLACE_STATS_SOURCE).toBe('/api/v1/marketplace/stats');
    expect(MARKETPLACE_PRODUCERS_SOURCE).toBe('/api/v1/marketplace/producers');
    expect(CONTENT_SEARCH_SOURCE).toBe('/api/v1/content/search');
  });

  it('sends farm_id only when one is supplied', () => {
    expect(dashboardPublicSource('soil', 'farm-1')).toBe('/dashboard/public/soil?farm_id=farm-1');
    expect(dashboardPublicSource('soil')).toBe('/dashboard/public/soil');
  });

  it('always sends the required content search term', () => {
    expect(contentSearchSource('soil', 20)).toBe('/api/v1/content/search?q=soil&limit=20');
    expect(contentSearchSource('soil')).toBe('/api/v1/content/search?q=soil');
  });
});

describe('surface requests', () => {
  it('returns the gateway payload without reshaping it', async () => {
    const payload = { status: 'success', auth_required: false, data: { total_projects: 3 } };
    fetchMock.mockResolvedValue(jsonResponse(payload));

    const result = await getDashboardPublic('analytics');
    expect(requestedUrl()).toBe(`${ORIGIN}/dashboard/public/analytics`);
    expect(result.ok).toBe(true);
    // Typed `unknown` on purpose: the contract declares no field, so the page
    // must not receive a shape the gateway never promised.
    if (result.ok) expect(result.data).toEqual(payload);
  });

  it('never turns a gateway failure into data', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'boom' }, 500));
    const result = await getDashboardPublic('full');
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.status).toBe(500);
      expect(result.error).toBe('boom');
    }
  });

  it('reports an offline device as status 0', async () => {
    fetchMock.mockRejectedValue(new Error('network down'));
    const result = await searchContent('soil');
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.status).toBe(0);
  });
});

describe('verificationOf', () => {
  it('trusts only a payload that claims verification', () => {
    expect(verificationOf({ verified: true })).toBe(true);
    expect(verificationOf({ schema_verified: true })).toBe(true);
    expect(verificationOf({ provenance: { verified: true } })).toBe(true);
  });

  it('does not certify a 200 response that asserts nothing', () => {
    // The public dashboard router answers 200 with hard-coded counters mixed in
    // with live ones, so HTTP success must not read as a measured value.
    expect(
      verificationOf({
        status: 'success',
        auth_required: false,
        data: { total_projects: 3, active_motors: 166 },
        timestamp: '2026-09-26T00:00:00+00:00',
      }),
    ).toBe(false);
    expect(verificationOf({ verified: false })).toBe(false);
    expect(verificationOf({ schema_verified: false })).toBe(false);
  });

  it('refuses to read a non-object payload as verified', () => {
    expect(verificationOf(null)).toBe(false);
    expect(verificationOf([{ verified: true }])).toBe(false);
    expect(verificationOf('verified')).toBe(false);
    expect(verificationOf(undefined)).toBe(false);
  });

  it('is not fooled by a truthy non-boolean', () => {
    expect(verificationOf({ verified: 'yes' })).toBe(false);
    expect(verificationOf({ verified: 1 })).toBe(false);
  });
});
