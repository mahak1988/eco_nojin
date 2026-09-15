/** Live runner for the mrv-metrics model (transparent MRV metrics with provenance).
 * Connects to the real MRV metrics endpoint
 * (POST /api/v1/mrv/metrics) which returns per-metric provenance badges
 * (real / simulated / no_data) and audit trail. */

import { useState, type FormEvent } from 'react';
import { BarChart3 } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import { KeyValues, Provenance, SectionCard, StateBanner, useLiveState } from './LivePanel';

const inputCls =
  'w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-ink-1 focus:border-leaf-400/60 focus:outline-none';

const PROV_CONFIG: Record<string, { label: string; cls: string }> = {
  real: { label: 'real', cls: 'bg-leaf-500/15 text-leaf-300' },
  simulated: { label: 'simulated', cls: 'bg-sand-500/15 text-sand-300' },
  no_data: { label: 'no_data', cls: 'bg-white/10 text-ink-3' },
};

/** A7 — live Transparent MRV metrics (mrv-metrics model). */
export default function MrvMetricsRunner() {
  const { lang } = useLang();
  const isFa = lang === 'fa';
  const metrics = useLiveState();
  const [region, setRegion] = useState('Tehran');
  const [year, setYear] = useState('2025');
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  const run = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setResult(null);
    const res = await metrics.run(() =>
      fetch('/api/v1/mrv/metrics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ region, year: Number(year) }),
      }).then((r) => r.json()),
    );
    if (res) setResult(res as Record<string, unknown>);
  };

  const provenance = result ? String(result.provenance ?? '') : '';
  const metricList = result?.metrics && Array.isArray(result.metrics) ? (result.metrics as Array<Record<string, unknown>>) : [];

  return (
    <div className="flex flex-col gap-4">
      <SectionCard
        title={
          <span className="inline-flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-aqua-400" aria-hidden />
            {isFa ? 'سنجه‌های شفاف MRV' : 'Transparent MRV metrics'}
          </span>
        }
        badge={result ? <Provenance source={provenance} /> : undefined}
      >
        <form onSubmit={run} className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3" dir="ltr">Region</span>
            <input type="text" value={region} onChange={(e) => setRegion(e.target.value)} className={inputCls} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3" dir="ltr">Year</span>
            <input type="number" value={year} onChange={(e) => setYear(e.target.value)} className={inputCls} />
          </label>
          <button
            type="submit"
            disabled={metrics.state === 'loading'}
            className="self-end rounded-xl bg-leaf-500 px-5 py-2.5 text-xs font-extrabold text-night-950 disabled:opacity-60"
          >
            {metrics.state === 'loading' ? (isFa ? 'دریافت…' : 'Fetching…') : isFa ? 'گرفتن سنجه‌ها' : 'Fetch metrics'}
          </button>
        </form>
        <div className="mt-3">
          <StateBanner state={metrics.state} error={metrics.error} retry={() => undefined} />
        </div>

        {result ? (
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-2xl font-extrabold text-aqua-300" dir="ltr">{String(result.region ?? '—')}</p>
              <p className="text-[11px] text-ink-3">{isFa ? 'منطقه' : 'Region'}</p>
            </div>
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-2xl font-extrabold text-leaf-300" dir="ltr">{String(result.year ?? '—')}</p>
              <p className="text-[11px] text-ink-3">{isFa ? 'سال' : 'Year'}</p>
            </div>
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-2xl font-extrabold text-ink-1" dir="ltr">{metricList.length}</p>
              <p className="text-[11px] text-ink-3">{isFa ? 'سنجه' : 'Metrics'}</p>
            </div>
          </div>
        ) : null}

        {metricList.length > 0 ? (
          <div className="mt-4 flex flex-col gap-2">
            <h4 className="text-[11px] font-bold text-ink-3">{isFa ? 'سنجه‌ها با برچسب منشأ' : 'Metrics with provenance'}</h4>
            {metricList.map((m, i) => {
              const prov = String(m.provenance ?? '').toLowerCase();
              const cfg = PROV_CONFIG[prov] ?? PROV_CONFIG.no_data;
              return (
                <div key={i} className="flex items-center justify-between gap-3 rounded-xl bg-black/20 px-4 py-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-extrabold text-ink-1" dir="ltr">{String(m.name ?? m.key ?? 'metric')}</p>
                    <p className="text-[11px] text-ink-3" dir="ltr">{String(m.value ?? '—')} {m.unit ? `· ${m.unit}` : ''}</p>
                  </div>
                  <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-[10px] font-bold ${cfg.cls}`}>{cfg.label}</span>
                </div>
              );
            })}
          </div>
        ) : null}
      </SectionCard>

      {result ? (
        <SectionCard title={isFa ? 'پاسخ کامل سرویس' : 'Full service response'}>
          <KeyValues data={result} />
        </SectionCard>
      ) : null}
    </div>
  );
}