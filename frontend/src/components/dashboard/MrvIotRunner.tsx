/** Live runner for the mrv-iot model (IoT sensor ingest with QA/QC).
 * Connects to the real IoT MRV endpoint
 * (POST /api/v1/mrv/iot/ingest) which returns a provenance-tagged
 * observation record with audit trail and QA/QC screening. */

import { useState, type FormEvent } from 'react';
import { Cpu } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import { KeyValues, Provenance, SectionCard, StateBanner, useLiveState } from './LivePanel';

const inputCls =
  'w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-ink-1 focus:border-leaf-400/60 focus:outline-none';

/** A7 — live IoT MRV (mrv-iot model). */
export default function MrvIotRunner() {
  const { lang } = useLang();
  const isFa = lang === 'fa';
  const ingest = useLiveState();
  const [sensorId, setSensorId] = useState('MQTT-TTN-001');
  const [metric, setMetric] = useState('soil_moisture');
  const [value, setValue] = useState('28.5');
  const [unit] = useState('%');
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  const run = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setResult(null);
    const res = await ingest.run(() =>
      fetch('/api/v1/mrv/iot/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sensor_id: sensorId,
          metric,
          value: Number(value),
          unit,
          ts: new Date().toISOString(),
        }),
      }).then((r) => r.json()),
    );
    if (res) setResult(res as Record<string, unknown>);
  };

  const provenance = result ? String(result.provenance ?? '') : '';
  const qa = result ? String(result.qa_status ?? '') : '';

  return (
    <div className="flex flex-col gap-4">
      <SectionCard
        title={
          <span className="inline-flex items-center gap-2">
            <Cpu className="h-4 w-4 text-aqua-400" aria-hidden />
            {isFa ? 'ورود حسگر IoT (MRV)' : 'IoT sensor ingest (MRV)'}
          </span>
        }
        badge={result ? <Provenance source={provenance} /> : undefined}
      >
        <form onSubmit={run} className="grid gap-3 sm:grid-cols-[1fr_1fr_1fr_auto]">
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3" dir="ltr">Sensor ID</span>
            <input type="text" value={sensorId} onChange={(e) => setSensorId(e.target.value)} className={inputCls} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3" dir="ltr">Metric</span>
            <input type="text" value={metric} onChange={(e) => setMetric(e.target.value)} className={inputCls} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3" dir="ltr">Value</span>
            <input type="number" step="any" value={value} onChange={(e) => setValue(e.target.value)} className={inputCls} />
          </label>
          <button
            type="submit"
            disabled={ingest.state === 'loading'}
            className="self-end rounded-xl bg-leaf-500 px-5 py-2.5 text-xs font-extrabold text-night-950 disabled:opacity-60"
          >
            {ingest.state === 'loading' ? (isFa ? 'در حال ارسال…' : 'Sending…') : isFa ? 'ارسال حسگر' : 'Ingest'}
          </button>
        </form>
        <div className="mt-3">
          <StateBanner state={ingest.state} error={ingest.error} retry={() => undefined} />
        </div>

        {result ? (
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-2xl font-extrabold text-aqua-300" dir="ltr">{String(result.metric ?? '—')}</p>
              <p className="text-[11px] text-ink-3">{isFa ? 'متریک' : 'Metric'}</p>
            </div>
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-2xl font-extrabold text-leaf-300" dir="ltr">{String(result.value ?? '—')}</p>
              <p className="text-[11px] text-ink-3">{isFa ? 'مقدار' : 'Value'}</p>
            </div>
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-sm font-extrabold text-ink-1">{qa || '—'}</p>
              <p className="text-[11px] text-ink-3">{isFa ? 'کیفیت داده' : 'QA status'}</p>
            </div>
          </div>
        ) : null}

        {result ? (
          <p className="mt-3 text-[11px] leading-5 text-ink-3">
            {isFa
              ? `ردپای حسابرسی: ${String(result.audit_id ?? '—')} — ${String(result.received_at ?? '')}`
              : `Audit trail: ${String(result.audit_id ?? '—')} — ${String(result.received_at ?? '')}`}
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