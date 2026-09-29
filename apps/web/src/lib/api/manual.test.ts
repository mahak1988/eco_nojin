import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { setApiBaseUrl } from './client';
import {
  columnsOf,
  formatCell,
  getManualClimateNormals,
  getManualCropCalendar,
  getManualSoilRegions,
  getManualStatus,
  getManualWeatherDaily,
  listManualSites,
  MANUAL_BASE,
  manualClimateNormalsSource,
  manualSiteSource,
  manualSitesPathGuard,
  manualWeatherDailySource,
  toRecords,
} from './manual';

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

describe('manual source paths', () => {
  it('derives every path from the published router prefix', () => {
    expect(MANUAL_BASE).toBe('/api/v1/manual');
    expect(manualSiteSource('12')).toBe('/api/v1/manual/sites/12');
    expect(manualWeatherDailySource('12')).toBe('/api/v1/manual/weather-daily/12');
    expect(manualClimateNormalsSource('12')).toBe('/api/v1/manual/climate-normals/12');
  });

  it('encodes a site id instead of concatenating it into the path', () => {
    expect(manualSiteSource('a b/../c')).toBe('/api/v1/manual/sites/a%20b%2F..%2Fc');
  });
});

describe('manual requests', () => {
  it('sends the gateway search parameter only when a query exists', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ count: 0, sites: [] }));
    await listManualSites();
    expect(requestedUrl()).toBe(`${ORIGIN}/api/v1/manual/sites`);

    await listManualSites('rasht');
    expect(requestedUrl(1)).toBe(`${ORIGIN}/api/v1/manual/sites?q=rasht`);
  });

  it('sends only the parameters the router declares', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ count: 0, rows: [] }));
    await getManualWeatherDaily('12', 200);
    expect(requestedUrl()).toBe(`${ORIGIN}/api/v1/manual/weather-daily/12?limit=200`);

    await getManualCropCalendar('تهران', 'گندم');
    expect(requestedUrl(1)).toBe(
      `${ORIGIN}/api/v1/manual/crop-calendar?province=${encodeURIComponent('تهران')}&crop_fa=${encodeURIComponent('گندم')}`,
    );

    await getManualSoilRegions();
    expect(requestedUrl(2)).toBe(`${ORIGIN}/api/v1/manual/soil-regions`);
  });

  it('never turns a gateway failure into data', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'not found' }, 404));
    const result = await getManualStatus();
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.status).toBe(404);
      expect(result.error).toBe('not found');
    }
  });

  it('reports an offline device as status 0 rather than an empty dataset', async () => {
    fetchMock.mockRejectedValue(new Error('network down'));
    const result = await getManualClimateNormals('12');
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.status).toBe(0);
  });
});

describe('record normalisation', () => {
  it('keeps only object rows and never invents one', () => {
    expect(toRecords([{ a: 1 }, 'nope', null, [1, 2], { b: 2 }])).toEqual([{ a: 1 }, { b: 2 }]);
    expect(toRecords(undefined)).toEqual([]);
    expect(toRecords({ a: 1 })).toEqual([]);
  });

  it('reads the column set back from the response in first-seen order', () => {
    expect(
      columnsOf([
        { site_id: 1, lat: 2 },
        { lon: 3, site_id: 4 },
      ]),
    ).toEqual(['site_id', 'lat', 'lon']);
    expect(columnsOf([])).toEqual([]);
  });

  it('renders a missing value as a neutral dash, never as a fabricated number', () => {
    expect(formatCell(null)).toBe('—');
    expect(formatCell(undefined)).toBe('—');
    expect(formatCell('')).toBe('—');
    expect(formatCell(0)).toBe('0');
    expect(formatCell(false)).toBe('false');
    expect(formatCell('rasht')).toBe('rasht');
  });
});

describe('manual site id guard', () => {
  it('accepts a numeric dataset key and rejects anything else', () => {
    expect(manualSitesPathGuard('12')).toBe(true);
    expect(manualSitesPathGuard('0')).toBe(true);
    expect(manualSitesPathGuard('12a')).toBe(false);
    expect(manualSitesPathGuard('')).toBe(false);
    expect(manualSitesPathGuard('-1')).toBe(false);
    expect(manualSitesPathGuard('1.5')).toBe(false);
  });
});
