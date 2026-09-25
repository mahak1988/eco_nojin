'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  canApplyUpdate,
  canCheckForUpdate,
  derivePhase,
  INITIAL_SIGNALS,
  type LifecycleSignals,
  PHASE_TOKENS,
  PHASE_TONES,
  type PwaPhaseTone,
  readUpdateRecord,
  type StorageLike,
  UPDATE_RECORD_KEY,
  type UpdateRecord,
  writeUpdateRecord,
} from './pwa-lifecycle';

export interface PwaUpdateLabels {
  metric: string;
  state: string;
  result: string;
  rows: string;
  live: string;
  unavailable: string;
  planned: string;
  error: string;
}

const TONE_LABEL_KEY: Record<PwaPhaseTone, keyof PwaUpdateLabels> = {
  ok: 'live',
  pending: 'planned',
  bad: 'unavailable',
  neutral: 'state',
};

const TONE_COLOR: Record<PwaPhaseTone, string> = {
  ok: 'text-forest',
  pending: 'text-copper',
  bad: 'text-clay',
  neutral: 'text-ink-soft',
};

const MAX_EVENTS = 12;
const APPLY_TIMEOUT_MS = 10_000;

interface ObservedEvent {
  id: number;
  token: string;
  at: string;
}

interface RegistrationFacts {
  controller: string | null;
  active: string | null;
  waiting: string | null;
  scope: string | null;
}

const NO_FACTS: RegistrationFacts = { controller: null, active: null, waiting: null, scope: null };

function localStore(): StorageLike | null {
  if (typeof window === 'undefined') return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function PwaUpdatePanel({ labels, locale }: { labels: PwaUpdateLabels; locale: string }) {
  const [signals, setSignals] = useState<LifecycleSignals>(INITIAL_SIGNALS);
  const [facts, setFacts] = useState<RegistrationFacts>(NO_FACTS);
  const [record, setRecord] = useState<UpdateRecord | null>(null);
  const [updateResult, setUpdateResult] = useState<boolean | null>(null);
  const [events, setEvents] = useState<ObservedEvent[]>([]);
  const registrationRef = useRef<ServiceWorkerRegistration | null>(null);
  const applyingRef = useRef(false);
  const reloadingRef = useRef(false);
  const timeoutRef = useRef<number | null>(null);
  const eventIdRef = useRef(0);

  const log = useCallback((token: string) => {
    setEvents((current) => {
      eventIdRef.current += 1;
      const next = [...current, { id: eventIdRef.current, token, at: new Date().toISOString() }];
      return next.length > MAX_EVENTS ? next.slice(next.length - MAX_EVENTS) : next;
    });
  }, []);

  const clearApplyTimeout = useCallback(() => {
    if (timeoutRef.current === null) return;
    window.clearTimeout(timeoutRef.current);
    timeoutRef.current = null;
  }, []);

  const readRegistration = useCallback(async (container: ServiceWorkerContainer) => {
    const registration = (await container.getRegistration()) ?? null;
    registrationRef.current = registration;
    setFacts({
      controller: container.controller?.scriptURL ?? null,
      active: registration?.active?.scriptURL ?? null,
      waiting: registration?.waiting?.scriptURL ?? null,
      scope: registration?.scope ?? null,
    });
    setRecord(readUpdateRecord(localStore()));
    setSignals((current) => ({
      ...current,
      checked: true,
      supported: true,
      registered: registration !== null,
      controller: Boolean(container.controller),
      waiting: Boolean(registration?.waiting),
      installing: Boolean(registration?.installing),
      failed: false,
    }));
    return registration;
  }, []);

  useEffect(() => {
    if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) {
      setSignals({ ...INITIAL_SIGNALS, checked: true, supported: false });
      return;
    }

    const container = navigator.serviceWorker;
    const attached = new WeakSet<ServiceWorker>();
    const subscriptions: Array<() => void> = [];
    let cancelled = false;

    const listen = (target: EventTarget, type: string, handler: EventListener) => {
      target.addEventListener(type, handler);
      subscriptions.push(() => target.removeEventListener(type, handler));
    };

    const onStateChange: EventListener = (event) => {
      const worker = event.target as ServiceWorker | null;
      if (!worker) return;
      log(`statechange: ${worker.state}`);
      const registration = registrationRef.current;
      setSignals((current) => ({
        ...current,
        checked: true,
        supported: true,
        registered: true,
        controller: Boolean(container.controller),
        waiting: Boolean(registration?.waiting),
        installing:
          worker.state === 'activated' || worker.state === 'redundant'
            ? false
            : Boolean(registration?.installing),
      }));
      setFacts((current) => ({
        ...current,
        controller: container.controller?.scriptURL ?? current.controller,
        active: registration?.active?.scriptURL ?? current.active,
        waiting: registration?.waiting?.scriptURL ?? current.waiting,
      }));
    };

    const attach = (worker: ServiceWorker | null) => {
      if (!worker || attached.has(worker)) return;
      attached.add(worker);
      listen(worker, 'statechange', onStateChange);
    };

    const onUpdateFound: EventListener = () => {
      log('updatefound');
      const registration = registrationRef.current;
      attach(registration?.installing ?? null);
      setSignals((current) => ({ ...current, installing: true, activatedNow: false }));
    };

    const onControllerChange: EventListener = () => {
      log('controllerchange');
      let applied: UpdateRecord | null = null;
      if (applyingRef.current) {
        applyingRef.current = false;
        clearApplyTimeout();
        applied = writeUpdateRecord(localStore(), {
          appliedAt: new Date().toISOString(),
          scope: registrationRef.current?.scope ?? container.controller?.scriptURL ?? '',
        });
        if (applied) setRecord(applied);
      }
      setFacts((current) => ({
        ...current,
        controller: container.controller?.scriptURL ?? current.controller,
      }));
      setSignals((current) => ({
        ...current,
        checked: true,
        supported: true,
        registered: true,
        controller: true,
        waiting: false,
        installing: false,
        applying: false,
        activatedNow: true,
      }));
      if (applied && !reloadingRef.current) {
        reloadingRef.current = true;
        window.location.reload();
      }
    };

    listen(container, 'controllerchange', onControllerChange);

    void readRegistration(container)
      .then((registration) => {
        if (cancelled || !registration) return;
        try {
          attach(registration.installing);
          attach(registration.waiting);
          attach(registration.active);
          listen(registration, 'updatefound', onUpdateFound);
        } catch {
          log('listener registration failed');
        }
      })
      .catch(() => {
        log('getRegistration() rejected');
        setSignals((current) => ({ ...current, checked: true, supported: true, failed: true }));
      });

    return () => {
      cancelled = true;
      clearApplyTimeout();
      for (const unsubscribe of subscriptions) unsubscribe();
    };
  }, [clearApplyTimeout, log, readRegistration]);

  const checkForUpdate = useCallback(async () => {
    const registration = registrationRef.current;
    setSignals((current) => ({ ...current, checking: true, failed: false, activatedNow: false }));
    log('registration.update()');
    try {
      const updated = await (registration ? registration.update() : Promise.resolve(undefined));
      setUpdateResult(Boolean(updated));
      setFacts((current) => ({
        ...current,
        waiting: registrationRef.current?.waiting?.scriptURL ?? null,
      }));
    } catch {
      log('registration.update() rejected');
      setSignals((current) => ({ ...current, failed: true }));
    } finally {
      setSignals((current) => ({ ...current, checking: false }));
    }
  }, [log]);

  const applyUpdate = useCallback(() => {
    const waiting = registrationRef.current?.waiting;
    if (!waiting) {
      log('registration.waiting missing');
      return;
    }
    clearApplyTimeout();
    applyingRef.current = true;
    setSignals((current) => ({ ...current, applying: true, activatedNow: false }));
    log('postMessage({ type: "SKIP_WAITING" })');
    waiting.postMessage({ type: 'SKIP_WAITING' });
    timeoutRef.current = window.setTimeout(() => {
      timeoutRef.current = null;
      if (!applyingRef.current) return;
      applyingRef.current = false;
      log('SKIP_WAITING timeout');
      setSignals((current) => ({ ...current, applying: false }));
    }, APPLY_TIMEOUT_MS);
  }, [clearApplyTimeout, log]);

  const phase = derivePhase(signals);
  const tone = PHASE_TONES[phase];
  const busy = signals.checking || signals.applying;
  const orUnavailable = (value: string | null) => value ?? labels.unavailable;

  const rows: Array<{ key: string; token: string; value: string; result: string | null }> = [
    {
      key: 'support',
      token: 'navigator.serviceWorker',
      value: signals.checked ? (signals.supported ? labels.live : labels.unavailable) : '—',
      result: null,
    },
    {
      key: 'controller',
      token: 'navigator.serviceWorker.controller',
      value: orUnavailable(facts.controller),
      result: null,
    },
    { key: 'scope', token: 'registration.scope', value: orUnavailable(facts.scope), result: null },
    {
      key: 'active',
      token: 'registration.active',
      value: orUnavailable(facts.active),
      result: null,
    },
    {
      key: 'waiting',
      token: 'registration.waiting',
      value: orUnavailable(facts.waiting),
      result: null,
    },
    {
      key: 'registration',
      token: 'navigator.serviceWorker.getRegistration()',
      value: !signals.checked
        ? '—'
        : signals.registered && !signals.failed
          ? labels.live
          : labels.unavailable,
      result: signals.registered ? facts.scope : null,
    },
    {
      key: 'update',
      token: 'registration.update()',
      value: !signals.checked
        ? '—'
        : signals.failed || !signals.registered
          ? labels.unavailable
          : signals.waiting
            ? labels.planned
            : labels.live,
      result: updateResult === null ? null : String(updateResult),
    },
    {
      key: 'record',
      token: `localStorage[${UPDATE_RECORD_KEY}]`,
      value: record?.appliedAt ?? labels.unavailable,
      result: record?.scope ?? null,
    },
  ];

  return (
    <div className="mt-6 space-y-4">
      <section className="card p-5" aria-labelledby="pwa-lifecycle-state">
        <h2 id="pwa-lifecycle-state" className="field-label">
          {labels.state}
        </h2>

        <p
          id="pwa-phase"
          role="status"
          aria-live="polite"
          aria-atomic="true"
          className="mt-3 flex flex-wrap items-center gap-2 text-sm"
        >
          <code className="num rounded bg-[var(--surface-2)] px-2 py-0.5 text-xs text-ink">
            {PHASE_TOKENS[phase]}
          </code>
          <span className={TONE_COLOR[tone]}>
            {phase === 'error' ? labels.error : labels[TONE_LABEL_KEY[tone]]}
          </span>
        </p>

        <div className="mt-4 overflow-x-auto">
          <table aria-busy={busy} className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-line text-ink-soft">
                <th scope="col" className="py-2 text-start font-medium">
                  {labels.metric}
                </th>
                <th scope="col" className="py-2 text-start font-medium">
                  {labels.state}
                </th>
                <th scope="col" className="py-2 text-start font-medium">
                  {labels.result}
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.key} className="border-b border-line/50">
                  <td className="num py-2 pe-4 text-xs text-ink">{row.token}</td>
                  <td className="py-2 pe-4 text-xs text-ink-soft">{row.value}</td>
                  <td className="num py-2 text-xs text-ink-faint">{row.result ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            className="btn btn-ghost"
            disabled={!canCheckForUpdate(signals)}
            onClick={() => void checkForUpdate()}
            aria-describedby="pwa-phase"
          >
            <code className="num text-xs">registration.update()</code>
          </button>
          <button
            type="button"
            className="btn btn-primary"
            disabled={!canApplyUpdate(signals)}
            onClick={applyUpdate}
            aria-describedby="pwa-phase"
          >
            <code className="num text-xs">SKIP_WAITING</code>
          </button>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => window.location.reload()}
            aria-describedby="pwa-phase"
          >
            <code className="num text-xs">location.reload()</code>
          </button>
        </div>
      </section>

      <section aria-labelledby="pwa-lifecycle-rows">
        <h2 id="pwa-lifecycle-rows" className="field-label">
          {labels.rows}
        </h2>
        {events.length === 0 ? (
          <p className="mt-3 text-sm text-ink-soft">{labels.unavailable}</p>
        ) : (
          <ol className="mt-3 divide-y divide-line rounded-[var(--radius-card)] border border-line bg-surface">
            {events.map((event) => (
              <li key={event.id} className="flex items-center justify-between gap-4 px-4 py-2">
                <code className="num text-xs text-ink">{event.token}</code>
                <time className="num text-xs text-ink-faint" dateTime={event.at}>
                  {new Date(event.at).toLocaleTimeString(locale)}
                </time>
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  );
}
