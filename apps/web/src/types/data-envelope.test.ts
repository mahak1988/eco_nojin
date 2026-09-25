import { describe, expect, it } from 'vitest';
import { createDataEnvelope, isDataEnvelope, type ProvenanceReference } from './data-envelope';

const liveSource: ProvenanceReference = {
  kind: 'api',
  id: 'platform-stats',
  uri: 'https://api.example.test/platform/stats',
  observedAt: '2026-09-24T00:00:00.000Z',
  version: '1.0',
  verified: true,
};

describe('DataEnvelope', () => {
  it('creates a typed live envelope with provenance', () => {
    const envelope = createDataEnvelope({
      status: 'live',
      data: { count: 12 },
      source: liveSource,
      observedAt: '2026-09-24T00:00:00.000Z',
      confidence: 0.95,
      unit: 'records',
    });

    expect(envelope.status).toBe('live');
    expect(envelope.data).toEqual({ count: 12 });
    expect(envelope.provenance[0]).toEqual(liveSource);
    expect(isDataEnvelope(envelope)).toBe(true);
  });

  it('requires an error for unavailable data', () => {
    const envelope = createDataEnvelope<unknown>({
      status: 'unavailable',
      data: null,
      source: { ...liveSource, verified: false },
      observedAt: '2026-09-24T00:00:00.000Z',
      error: { code: 'UPSTREAM_TIMEOUT', message: 'The source is unavailable.', retryable: true },
    });

    expect(envelope.status).toBe('unavailable');
    expect(envelope.data).toBeNull();
    if (envelope.status !== 'unavailable') {
      throw new Error('Expected unavailable envelope');
    }
    expect(envelope.error.retryable).toBe(true);
  });

  it('rejects invalid dates, confidence and verified demo data', () => {
    expect(() =>
      createDataEnvelope({
        status: 'live',
        data: 1,
        source: liveSource,
        observedAt: 'not-a-date',
      }),
    ).toThrow('Invalid ISO date');
    expect(() =>
      createDataEnvelope({
        status: 'live',
        data: 1,
        source: liveSource,
        observedAt: '2026-09-24T00:00:00.000Z',
        confidence: 1.5,
      }),
    ).toThrow('Confidence');
    expect(() =>
      createDataEnvelope({
        status: 'demo',
        data: 1,
        source: { ...liveSource, kind: 'demo', verified: true },
        observedAt: '2026-09-24T00:00:00.000Z',
      }),
    ).toThrow('Demo data cannot be marked verified');
  });
});
