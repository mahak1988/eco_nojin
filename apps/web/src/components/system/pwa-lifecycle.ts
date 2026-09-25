export const UPDATE_RECORD_KEY = 'econojin.pwa-update.v1';

export type PwaPhase =
  | 'probing'
  | 'unsupported'
  | 'error'
  | 'applying'
  | 'installing'
  | 'update-available'
  | 'not-registered'
  | 'checking'
  | 'activated'
  | 'active'
  | 'no-controller';

export interface LifecycleSignals {
  checked: boolean;
  supported: boolean;
  registered: boolean;
  controller: boolean;
  waiting: boolean;
  installing: boolean;
  checking: boolean;
  applying: boolean;
  failed: boolean;
  activatedNow: boolean;
}

export const INITIAL_SIGNALS: LifecycleSignals = {
  checked: false,
  supported: false,
  registered: false,
  controller: false,
  waiting: false,
  installing: false,
  checking: false,
  applying: false,
  failed: false,
  activatedNow: false,
};

export function derivePhase(signals: LifecycleSignals): PwaPhase {
  if (!signals.checked) return 'probing';
  if (!signals.supported) return 'unsupported';
  if (signals.failed) return 'error';
  if (signals.applying) return 'applying';
  if (signals.installing) return 'installing';
  if (signals.waiting) return 'update-available';
  if (!signals.registered) return 'not-registered';
  if (signals.checking) return 'checking';
  if (signals.activatedNow) return 'activated';
  if (signals.controller) return 'active';
  return 'no-controller';
}

export function canCheckForUpdate(signals: LifecycleSignals): boolean {
  return (
    signals.checked &&
    signals.supported &&
    signals.registered &&
    !signals.applying &&
    !signals.failed
  );
}

export function canApplyUpdate(signals: LifecycleSignals): boolean {
  return (
    signals.checked && signals.supported && signals.waiting && !signals.applying && !signals.failed
  );
}

export const PHASE_TOKENS: Record<PwaPhase, string> = {
  probing: 'getRegistration()',
  unsupported: 'navigator.serviceWorker',
  error: 'getRegistration()',
  applying: 'postMessage({ type: "SKIP_WAITING" })',
  installing: 'registration.installing',
  'update-available': 'registration.waiting',
  'not-registered': 'getRegistration() → undefined',
  checking: 'registration.update()',
  activated: 'controllerchange',
  active: 'navigator.serviceWorker.controller',
  'no-controller': 'controller: null',
};

export type PwaPhaseTone = 'ok' | 'pending' | 'bad' | 'neutral';

export const PHASE_TONES: Record<PwaPhase, PwaPhaseTone> = {
  probing: 'neutral',
  unsupported: 'bad',
  error: 'bad',
  applying: 'pending',
  installing: 'pending',
  'update-available': 'pending',
  'not-registered': 'bad',
  checking: 'neutral',
  activated: 'ok',
  active: 'ok',
  'no-controller': 'bad',
};

export interface UpdateRecord {
  appliedAt: string;
  scope: string;
}

export interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

const MAX_FUTURE_SKEW_MS = 60 * 60 * 1000;

function asPlainObject(value: unknown): Record<string, unknown> | null {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) return null;
  return value as Record<string, unknown>;
}

export function parseUpdateRecord(
  raw: string | null | undefined,
  now: number = Date.now(),
): UpdateRecord | null {
  if (typeof raw !== 'string' || raw.trim() === '') return null;
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return null;
  }
  const record = asPlainObject(parsed);
  if (!record) return null;
  const { appliedAt, scope } = record;
  if (typeof appliedAt !== 'string' || typeof scope !== 'string') return null;
  const appliedAtMs = Date.parse(appliedAt);
  if (!Number.isFinite(appliedAtMs)) return null;
  if (appliedAtMs - now > MAX_FUTURE_SKEW_MS) return null;
  const normalizedScope = scope.trim();
  if (normalizedScope === '') return null;
  return { appliedAt: new Date(appliedAtMs).toISOString(), scope: normalizedScope };
}

export function readUpdateRecord(storage: StorageLike | null, now?: number): UpdateRecord | null {
  if (!storage) return null;
  try {
    return parseUpdateRecord(storage.getItem(UPDATE_RECORD_KEY), now);
  } catch {
    return null;
  }
}

export function writeUpdateRecord(
  storage: StorageLike | null,
  record: UpdateRecord,
  now?: number,
): UpdateRecord | null {
  const valid = parseUpdateRecord(JSON.stringify(record), now);
  if (!storage || !valid) return null;
  try {
    storage.setItem(UPDATE_RECORD_KEY, JSON.stringify(valid));
  } catch {
    return null;
  }
  return valid;
}
