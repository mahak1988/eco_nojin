/** Live runner for the mrv-qa model (observation QA/QC with plausibility bands).
 * Connects to the real QA/QC endpoint
 * (POST /api/v1/mrv/qa/screen) which returns a screened observation
 * with accepted/suspect/rejected band and audit trail. */

import { useState, type FormEvent } from 'react';
import { ShieldCheck, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import { KeyValues, Provenance, SectionCard, StateBanner, useLiveState } from './LivePanel';

const inputCls =
  'w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-ink-1 focus:border-leaf-400/60 focus:outline-none';

const BAND_CONFIG: Record<string, { label: string; cls: string; icon: typeof CheckCircle2 }> = {
  accepted: { label: 'Accepted', cls: 'bg-leaf-500/15 text-leaf-300', icon: CheckCircle2 },
  suspect: { label: 'Suspect', cls: 'bg-sand-500/15 text-sand-300', icon: AlertTriangle },
  rejected: { label: 'Rejected', cls: 'bg-red-500/15 text-red-300', icon: XCircle },
};

/** A7 — live Observation QA/QC (mrv-qa model). */
export default function MrvQaRunner() {
  const { lang } = useLang();
  const isFa = lang === 'fa';
  const screen = useLiveState();
  const [metric, setMetric] = useState('soil_moisture');
  const [value, setValue] = useState('32.0');
  const [unit, setUnit] = useState('%');
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  const run = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setResult(null);
    const res = await screen.run(() =>
      fetch('/api/v1/mrv/qa/screen', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ metric, value: Number(value), unit }),
      }).then((r) => r.json()),
    );
    if (res) setResult(res as Record<string, unknown>);
  };

  const provenance = result ? String(result.provenance ?? '') : '';
  const band = result ? String(result.band ?? '').toLowerCase() : '';
  const bandCfg = BAND_CONFIG[band] ?? BAND_CONFIG.rejected;
  const BandIcon = bandCfg.icon;

  return (
    <div className="flex flex-col gap-4">
      <SectionCard
        title={
          <span className="inline-flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-aqua-400" aria-hidden />
            {isFa ? 'کیفیت مشاهدات (QA/QC)' : 'Observation QA/QC'}
          </span>
        }
        badge={result ? <Provenance source={provenance} /> : undefined}
      >
        <form onSubmit={run} className="grid gap-3 sm:grid-cols-[1fr_1fr_1fr_auto]">
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3" dir="ltr">Metric</span>
            <input type="text" value={metric} onChange={(e) => setMetric(e.target.value)} className={inputCls} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3" dir="ltr">Value</span>
            <input type="number" step="any" value={value} onChange={(e) => setValue(e.target.value)} className={inputCls} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3" dir="ltr">Unit</span>
            <input type="text" value={unit} onChange={(e) => setUnit(e.target.value)} className={inputCls} />
          </label>
          <button
            type="submit"
            disabled={screen.state === 'loading'}
            className="self-end rounded-xl bg-leaf-500 px-5 py-2.5 text-xs font-extrabold text-night-950 disabled:opacity-60"
          >
            {screen.state === 'loading' ? (isFa ? 'بررسی…' : 'Screening…') : isFa ? 'بررسی کیفیت' : 'Screen'}
          </button>
        </form>
        <div className="mt-3">
          <StateBanner state={screen.state} error={screen.error} retry={() => undefined} />
        </div>

        {result ? (
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-2xl font-extrabold text-aqua-300" dir="ltr">{String(result.metric ?? '—')}</p>
              <p className="text-[11px] text-ink-3">{isFa ? 'متریک' : 'Metric'}</p>
            </div>
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-2xl font-extrabold text-ink-1" dir="ltr">{String(result.value ?? '—')}</p>
              <p className="text-[11px] text-ink-3">{isFa ? 'مقدار' : 'Value'}</p>
            </div>
            <div className="rounded-xl bg-black/20 p-4 flex flex-col items-center justify-center gap-1">
              <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[10px] font-bold ${bandCfg.cls}`}>
                <BandIcon className="h-3.5 w-3.5" aria-hidden />
                {isFa ? (band === 'accepted' ? 'پذیرش' : band === 'suspect' ? 'مشکوک' : 'رد') : bandCfg.label}
              </span>
              <p className="text-[11px] text-ink-3">{isFa ? 'band کیفیت' : 'QA band'}</p>
            </div>
          </div>
        ) : null}

        {result ? (
          <p className="mt-3 text-[11px] leading-5 text-ink-3">
            {isFa
              ? `ردپای حسابرسی: ${String(result.audit_id ?? '—')}`
              : `Audit trail: ${String(result.audit_id ?? '—')}`}
          </p>
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