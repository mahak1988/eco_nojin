/** Live runner for the mrv-citizen model (offline-first citizen field reports).
 * Connects to the real citizen MRV endpoint
 * (POST /api/v1/mrv/citizen/report) which returns a provenance-tagged
 * field report with geolocation, crop, and observation metadata. */

import { useState, type FormEvent } from 'react';
import { User, MapPin, Camera, Leaf } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import { KeyValues, Provenance, SectionCard, StateBanner, useLiveState } from './LivePanel';

const inputCls =
  'w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-ink-1 focus:border-leaf-400/60 focus:outline-none';

/** A7 — live Citizen MRV (mrv-citizen model). */
export default function MrvCitizenRunner() {
  const { lang } = useLang();
  const isFa = lang === 'fa';
  const submit = useLiveState();
  const [location, setLocation] = useState('Tehran, Iran');
  const [crop, setCrop] = useState('wheat');
  const [observation, setObservation] = useState('healthy');
  const [notes, setNotes] = useState('');
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  const run = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setResult(null);
    const res = await submit.run(() =>
      fetch('/api/v1/mrv/citizen/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location,
          crop,
          observation,
          notes,
          ts: new Date().toISOString(),
        }),
      }).then((r) => r.json()),
    );
    if (res) setResult(res as Record<string, unknown>);
  };

  const provenance = result ? String(result.provenance ?? '') : '';
  const status = result ? String(result.status ?? '') : '';

  return (
    <div className="flex flex-col gap-4">
      <SectionCard
        title={
          <span className="inline-flex items-center gap-2">
            <User className="h-4 w-4 text-aqua-400" aria-hidden />
            {isFa ? 'گزارش میدانی شهروندی (MRV)' : 'Citizen field report (MRV)'}
          </span>
        }
        badge={result ? <Provenance source={provenance} /> : undefined}
      >
        <form onSubmit={run} className="flex flex-col gap-3">
          <label className="flex flex-col gap-1">
            <span className="flex items-center gap-1.5 text-[11px] font-bold text-ink-3">
              <MapPin className="h-3.5 w-3.5" aria-hidden />
              {isFa ? 'مکان' : 'Location'}
            </span>
            <input type="text" value={location} onChange={(e) => setLocation(e.target.value)} className={inputCls} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="flex items-center gap-1.5 text-[11px] font-bold text-ink-3">
              <Leaf className="h-3.5 w-3.5" aria-hidden />
              {isFa ? 'نوع گیاه' : 'Crop'}
            </span>
            <input type="text" value={crop} onChange={(e) => setCrop(e.target.value)} className={inputCls} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="flex items-center gap-1.5 text-[11px] font-bold text-ink-3">
              <Camera className="h-3.5 w-3.5" aria-hidden />
              {isFa ? ' مشاهده' : 'Observation'}
            </span>
            <input type="text" value={observation} onChange={(e) => setObservation(e.target.value)} className={inputCls} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3">{isFa ? 'یادداشت‌ها' : 'Notes'}</span>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-ink-1 outline-none focus:border-leaf-400/60"
            />
          </label>
          <button
            type="submit"
            disabled={submit.state === 'loading'}
            className="self-start rounded-xl bg-leaf-500 px-5 py-2.5 text-xs font-extrabold text-night-950 disabled:opacity-60"
          >
            {submit.state === 'loading' ? (isFa ? 'در حال ارسال…' : 'Sending…') : isFa ? 'ارسال گزارش' : 'Submit report'}
          </button>
        </form>
        <div className="mt-3">
          <StateBanner state={submit.state} error={submit.error} retry={() => undefined} />
        </div>

        {result ? (
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-2xl font-extrabold text-aqua-300" dir="ltr">{String(result.report_id ?? '—')}</p>
              <p className="text-[11px] text-ink-3">{isFa ? 'شماره گزارش' : 'Report ID'}</p>
            </div>
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-sm font-extrabold text-ink-1">{status || '—'}</p>
              <p className="text-[11px] text-ink-3">{isFa ? 'وضعیت' : 'Status'}</p>
            </div>
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-sm font-extrabold text-ink-1">{String(result.offline_first ?? '—')}</p>
              <p className="text-[11px] text-ink-3">{isFa ? 'آفلاین-اول' : 'Offline-first'}</p>
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