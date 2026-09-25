import { describe, expect, it } from 'vitest';

import {
  canApplyUpdate,
  canCheckForUpdate,
  derivePhase,
  INITIAL_SIGNALS,
  type LifecycleSignals,
  PHASE_TOKENS,
  parseUpdateRecord,
  readUpdateRecord,
  type StorageLike,
  UPDATE_RECORD_KEY,
  writeUpdateRecord,
} from './pwa-lifecycle';

const NOW = Date.parse('2026-09-25T12:00:00.000Z');

function signals(overrides: Partial<LifecycleSignals> = {}): LifecycleSignals {
  return { ...INITIAL_SIGNALS, checked: true, supported: true, registered: true, ...overrides };
}

function fakeStorage(
  initial: Record<string, string> = {},
): StorageLike & { data: Record<string, string> } {
  const data = { ...initial };
  return {
    data,
    getItem(key) {
      return Object.hasOwn(data, key) ? data[key] : null;
    },
    setItem(key, value) {
      data[key] = value;
    },
  };
}

describe('derivePhase', () => {
  it('probes before the registration has been read', () => {
    expect(derivePhase(INITIAL_SIGNALS)).toBe('probing');
  });

  it('reports an unsupported browser before anything else', () => {
    expect(derivePhase({ ...INITIAL_SIGNALS, checked: true, supported: false })).toBe(
      'unsupported',
    );
  });

  it('prefers a failed read over every other signal', () => {
    expect(derivePhase(signals({ failed: true, waiting: true, controller: true }))).toBe('error');
  });

  it('keeps a pending activation visible while it is in flight', () => {
    expect(derivePhase(signals({ applying: true, waiting: true }))).toBe('applying');
  });

  it('reports an installing worker', () => {
    expect(derivePhase(signals({ installing: true, checking: true }))).toBe('installing');
  });

  it('reports a waiting worker even while a check is running', () => {
    expect(derivePhase(signals({ waiting: true, checking: true }))).toBe('update-available');
  });

  it('separates a fresh controller from a steady one', () => {
    expect(derivePhase(signals({ activatedNow: true, controller: true }))).toBe('activated');
    expect(derivePhase(signals({ controller: true }))).toBe('active');
  });

  it('separates a missing registration from a controlled page', () => {
    expect(derivePhase(signals({ registered: false, controller: false }))).toBe('not-registered');
    expect(derivePhase(signals({ registered: true, controller: false }))).toBe('no-controller');
  });

  it('never claims an active worker without a controller', () => {
    expect(derivePhase(signals({ controller: false }))).toBe('no-controller');
  });
});

describe('action availability', () => {
  it('never offers an action before the first read', () => {
    expect(canCheckForUpdate(INITIAL_SIGNALS)).toBe(false);
    expect(canApplyUpdate(INITIAL_SIGNALS)).toBe(false);
  });

  it('offers a check on a registered, controlled service worker', () => {
    expect(canCheckForUpdate(signals({ controller: true }))).toBe(true);
    expect(canApplyUpdate(signals({ controller: true }))).toBe(false);
  });

  it('offers no check when no registration exists', () => {
    expect(canCheckForUpdate(signals({ registered: false }))).toBe(false);
  });

  it('offers the activation only for a waiting worker and blocks it while applying', () => {
    expect(canApplyUpdate(signals({ waiting: true }))).toBe(true);
    expect(canApplyUpdate(signals({ waiting: true, applying: true }))).toBe(false);
    expect(canCheckForUpdate(signals({ waiting: true, applying: true }))).toBe(false);
  });
});

describe('phase tokens', () => {
  it('names the real web-platform signal for every phase', () => {
    for (const [phase, token] of Object.entries(PHASE_TOKENS)) {
      expect(token.length).toBeGreaterThan(0);
      expect(phase.length).toBeGreaterThan(0);
    }
    expect(PHASE_TOKENS['update-available']).toBe('registration.waiting');
    expect(PHASE_TOKENS['not-registered']).toBe('getRegistration() → undefined');
    expect(PHASE_TOKENS.applying).toContain('SKIP_WAITING');
    expect(PHASE_TOKENS.activated).toBe('controllerchange');
  });
});

describe('parseUpdateRecord', () => {
  it('accepts a well-formed record and normalises the timestamp', () => {
    const record = parseUpdateRecord(
      JSON.stringify({ appliedAt: '2026-09-25T11:59:00Z', scope: ' https://x.test/ ' }),
      NOW,
    );
    expect(record).toEqual({ appliedAt: '2026-09-25T11:59:00.000Z', scope: 'https://x.test/' });
  });

  it.each([
    ['null', null],
    ['empty string', ''],
    ['blank string', '   '],
    ['broken json', '{appliedAt:'],
    ['a json array', '[]'],
    ['a json scalar', '"appliedAt"'],
    ['a null payload', 'null'],
    ['a missing scope', '{"appliedAt":"2026-09-25T11:59:00.000Z"}'],
    ['a missing appliedAt', '{"scope":"/"}'],
    ['a non-string appliedAt', '{"appliedAt":1758801540000,"scope":"/"}'],
    ['a non-string scope', '{"appliedAt":"2026-09-25T11:59:00.000Z","scope":42}'],
    ['an unparsable date', '{"appliedAt":"not-a-date","scope":"/"}'],
    ['a blank scope', '{"appliedAt":"2026-09-25T11:59:00.000Z","scope":"   "}'],
    ['a far-future date', '{"appliedAt":"2027-09-25T11:59:00.000Z","scope":"/"}'],
  ])('rejects %s', (_label, raw) => {
    expect(parseUpdateRecord(raw, NOW)).toBeNull();
  });

  it('ignores unknown extra fields instead of trusting them', () => {
    const record = parseUpdateRecord(
      '{"appliedAt":"2026-09-25T11:59:00.000Z","scope":"/","updateAvailable":true}',
      NOW,
    );
    expect(record).toEqual({ appliedAt: '2026-09-25T11:59:00.000Z', scope: '/' });
  });
});

describe('readUpdateRecord', () => {
  it('returns null without storage', () => {
    expect(readUpdateRecord(null, NOW)).toBeNull();
  });

  it('does not pass invalid stored state through', () => {
    const storage = fakeStorage({ [UPDATE_RECORD_KEY]: '{"appliedAt":"nope"}' });
    expect(readUpdateRecord(storage, NOW)).toBeNull();
  });

  it('survives a storage that throws', () => {
    const storage: StorageLike = {
      getItem() {
        throw new Error('SecurityError');
      },
      setItem() {},
    };
    expect(readUpdateRecord(storage, NOW)).toBeNull();
  });

  it('reads a valid stored record', () => {
    const storage = fakeStorage({
      [UPDATE_RECORD_KEY]: '{"appliedAt":"2026-09-25T11:00:00.000Z","scope":"/fa"}',
    });
    expect(readUpdateRecord(storage, NOW)).toEqual({
      appliedAt: '2026-09-25T11:00:00.000Z',
      scope: '/fa',
    });
  });
});

describe('writeUpdateRecord', () => {
  it('stores a validated record', () => {
    const storage = fakeStorage();
    const written = writeUpdateRecord(
      storage,
      { appliedAt: '2026-09-25T11:00:00.000Z', scope: '/fa' },
      NOW,
    );
    expect(written).not.toBeNull();
    expect(readUpdateRecord(storage, NOW)).toEqual(written);
  });

  it('refuses to write an invalid record', () => {
    const storage = fakeStorage();
    expect(writeUpdateRecord(storage, { appliedAt: 'soon', scope: '/fa' }, NOW)).toBeNull();
    expect(storage.data[UPDATE_RECORD_KEY]).toBeUndefined();
  });

  it('reports a write failure instead of throwing', () => {
    const storage: StorageLike = {
      getItem: () => null,
      setItem() {
        throw new Error('QuotaExceededError');
      },
    };
    expect(
      writeUpdateRecord(storage, { appliedAt: '2026-09-25T11:00:00.000Z', scope: '/' }, NOW),
    ).toBeNull();
  });
});
