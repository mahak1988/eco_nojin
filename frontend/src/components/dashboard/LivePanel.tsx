/** Shared UI for live dashboard pages: request state with actionable hints
 * (login / admin / credentials), provenance badge, key-value view. */

import { useState, type ReactNode } from 'react';
import { RotateCw, TriangleAlert, CheckCircle2, LogIn, ShieldAlert, KeyRound } from 'lucide-react';
import { Link } from 'react-router-dom';
import { ApiError, classifyError, type ErrorKind } from '../../lib/hydromaApi';
import { useLang } from '../../i18n/LanguageContext';

type State = 'idle' | 'loading' | 'error' | 'done';

export function useLiveState(): {
  state: State;
  error: string | null;
  kind: ErrorKind | null;
  run: <T>(fn: () => Promise<T>) => Promise<T | null>;
  reset: () => void;
} {
  const [state, setState] = useState<State>('idle');
  const [error, setError] = useState<string | null>(null);
  const [kind, setKind] = useState<ErrorKind | null>(null);
  const run = async <T,>(fn: () => Promise<T>): Promise<T | null> => {
    setState('loading');
    setError(null);
    setKind(null);
    try {
      const result = await fn();
      setState('done');
      return result;
    } catch (err) {
      setKind(classifyError(err));
      const message =
        err instanceof ApiError
          ? `${err.message}${err.detail ? ' — ' + JSON.stringify(err.detail).slice(0, 200) : ''}`
          : err instanceof Error
            ? err.message
            : 'unknown error';
      setError(message);
      setState('error');
      return null;
    }
  };
  return { state, error, kind, run, reset: () => setState('idle') };
}

function KindHint({ kind }: { kind: ErrorKind | null }) {
  const { lang } = useLang();
  const isFa = lang === 'fa';
  if (kind === 'csrf') {
    return (
      <span className="flex flex-wrap items-center gap-2 text-[11px] font-bold text-sand-300">
        <LogIn className="h-3.5 w-3.5" aria-hidden />
        {isFa ? 'این درخواست نیازمند ورود است (Bearer).' : 'This request requires login (Bearer).'}
        <Link to="/dashboard/login" className="rounded-full bg-leaf-500/20 px-3 py-1 text-leaf-300 hover:bg-leaf-500/30">
          {isFa ? 'ورود / ثبت‌نام' : 'Login / Register'}
        </Link>
      </span>
    );
  }
  if (kind === 'role') {
    return (
      <span className="flex flex-wrap items-center gap-2 text-[11px] font-bold text-sand-300">
        <ShieldAlert className="h-3.5 w-3.5" aria-hidden />
        {isFa
          ? 'این موتور نیازمند نقش admin است (حساب مدیر پروژه). با حساب مدیر وارد شوید.'
          : 'This motor requires the admin role (project admin account).'}
      </span>
    );
  }
  if (kind === 'validation') {
    return (
      <span className="flex items-center gap-2 text-[11px] font-bold text-sand-300">
        <KeyRound className="h-3.5 w-3.5" aria-hidden />
        {isFa ? 'پارامترهای ورودی را کامل/درست کنید.' : 'Complete or correct the input parameters.'}
      </span>
    );
  }
  return null;
}

export function StateBanner({
  state,
  error,
  kind,
  retry,
}: {
  state: State;
  error: string | null;
  kind?: ErrorKind | null;
  retry: () => void;
}) {
  const { lang } = useLang();
  const isFa = lang === 'fa';
  if (state === 'loading') {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-xs font-bold text-ink-2">
        <RotateCw className="h-4 w-4 animate-spin text-aqua-400" aria-hidden />
        {isFa ? 'در حال دریافت از درگاه…' : 'Fetching from the gateway…'}
      </div>
    );
  }
  if (state === 'error') {
    return (
      <div className="flex flex-col gap-2 rounded-xl border border-red-400/30 bg-red-400/10 px-4 py-3">
        <span className="flex items-center gap-2 text-xs font-bold text-red-300">
          <TriangleAlert className="h-4 w-4" aria-hidden />
          {isFa ? 'خطا — پاسخ درگاه:' : 'Error — gateway response:'}
        </span>
        <code className="break-all text-[11px] text-red-200/80" dir="ltr">
          {error}
        </code>
        {kind ? <KindHint kind={kind} /> : null}
        <button
          type="button"
          onClick={retry}
          className="w-fit rounded-full bg-white/10 px-3 py-1 text-[11px] font-bold text-emerald-50 hover:bg-white/15"
        >
          {isFa ? 'تلاش دوباره' : 'Retry'}
        </button>
      </div>
    );
  }
  if (state === 'done') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-leaf-500/12 px-3 py-1 text-[11px] font-bold text-leaf-300">
        <CheckCircle2 className="h-3.5 w-3.5" aria-hidden />
        {isFa ? 'دریافت شد' : 'Received'}
      </span>
    );
  }
  return null;
}

/** Provenance badge — the engine's honest real / simulated / no_data rule. */
export function Provenance({ source }: { source: string | undefined }) {
  const { lang } = useLang();
  const isFa = lang === 'fa';
  const map: Record<string, { label: string; cls: string }> = {
    real: { label: isFa ? 'واقعی' : 'real', cls: 'bg-leaf-500/15 text-leaf-300' },
    simulated: { label: isFa ? 'شبیه‌سازی' : 'simulated', cls: 'bg-sand-500/15 text-sand-300' },
    no_data: { label: isFa ? 'بدون داده' : 'no_data', cls: 'bg-white/10 text-ink-3' },
  };
  const key = (source ?? '').toLowerCase();
  const entry = map[key] ?? map.no_data;
  return <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${entry.cls}`}>{entry.label}</span>;
}

/** Renders an object as a compact definition list. */
export function KeyValues({ data }: { data: Record<string, unknown> }) {
  const rows: { key: string; value: string }[] = [];
  for (const [key, value] of Object.entries(data)) {
    if (value === null || value === undefined) continue;
    if (typeof value === 'object') {
      rows.push({ key, value: JSON.stringify(value).slice(0, 220) });
    } else {
      rows.push({ key, value: String(value) });
    }
  }
  if (rows.length === 0) return null;
  return (
    <dl className="grid gap-x-5 gap-y-2 sm:grid-cols-2">
      {rows.map((row) => (
        <div key={row.key} className="flex items-baseline justify-between gap-3 rounded-lg bg-black/20 px-3 py-2">
          <dt className="text-[11px] font-bold text-ink-3" dir="ltr">
            {row.key}
          </dt>
          <dd className="truncate text-right text-xs font-bold text-ink-1" dir="ltr" title={row.value}>
            {row.value}
          </dd>
        </div>
      ))}
    </dl>
  );
}

export function SectionCard({ title, children, badge }: { title: ReactNode; children: ReactNode; badge?: ReactNode }) {
  return (
    <section className="glass rounded-[21px] p-5">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <h2 className="text-sm font-extrabold text-ink-1">{title}</h2>
        {badge}
      </div>
      {children}
    </section>
  );
}
