/** Live runner for the mrv-satellite model (Copernicus Sentinel-2 NDVI).
 * Connects to the real satellite analysis endpoint
 * (POST /api/v1/satellite/analyze) which returns NDVI/EVI/SAVI with a
 * transparent data-source label (copernicus vs simulated). */

import { useState, type FormEvent } from 'react';
import { Satellite } from 'lucide-react';
import { satelliteApi } from '../../lib/hydromaApi';
import { useLang } from '../../i18n/LanguageContext';
import { KeyValues, Provenance, SectionCard, StateBanner, useLiveState } from './LivePanel';

function num(data: Record<string, unknown>, key: string): number | null {
  const v = data[key];
  return typeof v === 'number' ? v : null;
}

/** A2 — live Sentinel-2 NDVI (mrv-satellite model). */
export default function MrvSatelliteRunner() {
  const { lang } = useLang();
  const isFa = lang === 'fa';
  const analyze = useLiveState();
  const [lat, setLat] = useState('35.70');
  const [lon, setLon] = useState('51.40');
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  const inputCls =
    'w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-ink-1 focus:border-leaf-400/60 focus:outline-none';

  const run = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setResult(null);
    const res = await analyze.run(() => satelliteApi.analyze(Number(lat), Number(lon)));
    if (res) setResult(res as Record<string, unknown>);
  };

  const ndvi = result ? num(result, 'ndvi') : null;
  const evi = result ? num(result, 'evi') : null;
  const savi = result ? num(result, 'savi') : null;
  const source = result ? String(result.data_source ?? '') : '';

  return (
    <div className="flex flex-col gap-4">
      <SectionCard
        title={
          <span className="inline-flex items-center gap-2">
            <Satellite className="h-4 w-4 text-aqua-400" aria-hidden />
            {isFa ? 'NDVI زنده — Sentinel-2 (Copernicus)' : 'Live NDVI — Sentinel-2 (Copernicus)'}
          </span>
        }
        badge={result ? <Provenance source={source} /> : undefined}
      >
        <form onSubmit={run} className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3" dir="ltr">Lat</span>
            <input type="number" step="0.01" value={lat} onChange={(e) => setLat(e.target.value)} className={inputCls} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3" dir="ltr">Lon</span>
            <input type="number" step="0.01" value={lon} onChange={(e) => setLon(e.target.value)} className={inputCls} />
          </label>
          <button
            type="submit"
            disabled={analyze.state === 'loading'}
            className="self-end rounded-xl bg-leaf-500 px-5 py-2.5 text-xs font-extrabold text-night-950 disabled:opacity-60"
          >
            {analyze.state === 'loading' ? (isFa ? 'در حال تحلیل…' : 'Analyzing…') : isFa ? 'تحلیل ماهواره' : 'Analyze'}
          </button>
        </form>
        <div className="mt-3">
          <StateBanner state={analyze.state} error={analyze.error} retry={() => undefined} />
        </div>

        {result ? (
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-2xl font-extrabold text-leaf-300" dir="ltr">{ndvi !== null ? ndvi.toFixed(3) : '—'}</p>
              <p className="text-[11px] text-ink-3">NDVI</p>
            </div>
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-2xl font-extrabold text-aqua-300" dir="ltr">{evi !== null ? evi.toFixed(3) : '—'}</p>
              <p className="text-[11px] text-ink-3">EVI</p>
            </div>
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-2xl font-extrabold text-sand-300" dir="ltr">{savi !== null ? savi.toFixed(3) : '—'}</p>
              <p className="text-[11px] text-ink-3">SAVI</p>
            </div>
          </div>
        ) : null}

        {result ? (
          <p className="mt-3 text-[11px] leading-5 text-ink-3">
            {isFa
              ? `وضعیت پوشش گیاهی: ${String(result.vegetation_health ?? '—')} — ${String(result.recommendation ?? '')}`
              : `Vegetation health: ${String(result.vegetation_health ?? '—')} — ${String(result.recommendation ?? '')}`}
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
