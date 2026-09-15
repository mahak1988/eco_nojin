/** Live runner for the full scientific chain (sim-orchestrator model).
 * Executes the REAL chain — RUSLE erosion → RothC-26.3 soil carbon →
 * AquaCrop yield — against POST /api/v1/motors/chain with real weather
 * (Open-Meteo ERA5) and SoilGrids data. Long-running (~20-120 s). */

import { useState, type FormEvent } from 'react';
import { FlaskConical, Timer } from 'lucide-react';
import { chainApi } from '../../lib/hydromaApi';
import { useLang } from '../../i18n/LanguageContext';
import { KeyValues, SectionCard, StateBanner, useLiveState } from './LivePanel';

const inputCls =
  'w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-ink-1 focus:border-leaf-400/60 focus:outline-none';

const CROPS = ['wheat', 'maize', 'barley', 'potato', 'cotton', 'tomato'];
const PRACTICES = ['none', 'contour', 'terrace'];

/** Chain orchestrator (sim-orchestrator model). */
export default function ChainRunner() {
  const { lang } = useLang();
  const isFa = lang === 'fa';
  const chain = useLiveState();
  const [lat, setLat] = useState('35.70');
  const [lon, setLon] = useState('51.40');
  const [crop, setCrop] = useState('wheat');
  const [years, setYears] = useState('20');
  const [slope, setSlope] = useState('10');
  const [practice, setPractice] = useState('none');
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  const run = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setResult(null);
    const res = await chain.run(() =>
      chainApi.motors({
        lat: Number(lat),
        lon: Number(lon),
        crop,
        years: Number(years),
        slope_pct: Number(slope),
        practice,
      }),
    );
    if (res) setResult(res as Record<string, unknown>);
  };

  return (
    <div className="flex flex-col gap-4">
      <SectionCard
        title={
          <span className="inline-flex items-center gap-2">
            <FlaskConical className="h-4 w-4 text-leaf-400" aria-hidden />
            {isFa ? 'زنجیرهٔ علمی زنده — RUSLE → RothC → AquaCrop' : 'Live scientific chain — RUSLE → RothC → AquaCrop'}
          </span>
        }
        badge={
          <span className="inline-flex items-center gap-1 rounded-full bg-sand-500/15 px-2.5 py-0.5 text-[10px] font-bold text-sand-300">
            <Timer className="h-3 w-3" aria-hidden />
            {isFa ? '۲۰ تا ۱۲۰ ثانیه' : '20-120 s'}
          </span>
        }
      >
        <form onSubmit={run} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3" dir="ltr">Lat</span>
            <input type="number" step="0.01" value={lat} onChange={(e) => setLat(e.target.value)} className={inputCls} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3" dir="ltr">Lon</span>
            <input type="number" step="0.01" value={lon} onChange={(e) => setLon(e.target.value)} className={inputCls} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3">{isFa ? 'گیاه' : 'Crop'}</span>
            <select value={crop} onChange={(e) => setCrop(e.target.value)} className={inputCls}>
              {CROPS.map((c) => (
                <option key={c} value={c} className="bg-[#0b1526]">{c}</option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3">{isFa ? 'سال‌های شبیهسازی' : 'Years'}</span>
            <input type="number" value={years} onChange={(e) => setYears(e.target.value)} className={inputCls} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3">{isFa ? 'شیب (%)' : 'Slope (%)'}</span>
            <input type="number" step="0.1" value={slope} onChange={(e) => setSlope(e.target.value)} className={inputCls} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3">{isFa ? 'عملحفاظتی' : 'Practice'}</span>
            <select value={practice} onChange={(e) => setPractice(e.target.value)} className={inputCls}>
              {PRACTICES.map((p) => (
                <option key={p} value={p} className="bg-[#0b1526]">{p}</option>
              ))}
            </select>
          </label>
          <button
            type="submit"
            disabled={chain.state === 'loading'}
            className="self-end rounded-xl bg-leaf-500 px-5 py-2.5 text-xs font-extrabold text-night-950 disabled:opacity-60 sm:col-span-2 lg:col-span-3"
          >
            {chain.state === 'loading'
              ? (isFa ? 'در حال اجرای زنجیره (تا ۲ دقیقه)…' : 'Running the chain (up to 2 min)…')
              : isFa ? 'اجرای زنجیرهٔ علمی' : 'Run scientific chain'}
          </button>
        </form>
        <div className="mt-3">
          <StateBanner state={chain.state} error={chain.error} retry={() => undefined} />
        </div>
        <p className="mt-2 text-[11px] leading-5 text-ink-3">
          {isFa
            ? 'ورودی هواشناسی از ERA5 (Open-Meteo) و خاک از SoilGrids — هر خروجی با برچسب منبع داده.'
            : 'Weather from ERA5 (Open-Meteo), soil from SoilGrids — every output carries a data-source label.'}
        </p>
      </SectionCard>

      {result ? (
        <>
          <SectionCard title={isFa ? 'خروجی زنجیره' : 'Chain output'}>
            <KeyValues data={{
              cache_hit: result.cache_hit,
              status: result.status,
              location: result.location,
              data_sources: result.data_sources,
            }} />
          </SectionCard>
          {result.erosion ? (
            <SectionCard title={isFa ? 'فرسایش (RUSLE)' : 'Erosion (RUSLE)'}>
              <KeyValues data={result.erosion as Record<string, unknown>} />
            </SectionCard>
          ) : null}
          {result.rothc ? (
            <SectionCard title={isFa ? 'کربن خاک (RothC-26.3)' : 'Soil carbon (RothC-26.3)'}>
              <KeyValues data={result.rothc as Record<string, unknown>} />
            </SectionCard>
          ) : null}
          {result.aquacrop ? (
            <SectionCard title={isFa ? 'عملکرد (AquaCrop)' : 'Yield (AquaCrop)'}>
              <KeyValues data={result.aquacrop as Record<string, unknown>} />
            </SectionCard>
          ) : null}
          {result.calibration ? (
            <SectionCard title={isFa ? 'کالیبراسیون (KGE)' : 'Calibration (KGE)'}>
              <KeyValues data={result.calibration as Record<string, unknown>} />
            </SectionCard>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
