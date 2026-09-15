import { useState, type FormEvent } from 'react';
import Seo from '../../../components/ui/Seo';
import { chainApi, type ChainRequest } from '../../../lib/hydromaApi';
import { useLang } from '../../../i18n/LanguageContext';
import {
  KeyValues,
  Provenance,
  SectionCard,
  StateBanner,
  useLiveState,
} from '../../../components/dashboard/LivePanel';

const RESULT_SECTIONS = [
  'erosion',
  'swat',
  'water',
  'flood',
  'optimization',
  'rothc',
  'aquacrop',
  'calibration',
] as const;

/** A4 — live scientific chain: RUSLE → SWAT → RothC → AquaCrop via motors/chain. */
export default function LiveChainPage() {
  const { lang, t } = useLang();
  const isFa = lang === 'fa';
  const [lat, setLat] = useState('31.32');
  const [lon, setLon] = useState('50.70');
  const [crop, setCrop] = useState('wheat');
  const [areaHa, setAreaHa] = useState('10');
  const [slope, setSlope] = useState('3');
  const chain = useLiveState();
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  const inputCls =
    'w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-ink-1 focus:border-leaf-400/60 focus:outline-none';

  const run = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const body: ChainRequest = {
      lat: Number(lat),
      lon: Number(lon),
      crop,
      slope_pct: Number(slope),
      optimize: true,
    };
    const res = await chain.run(() => chainApi.motors(body));
    if (res) setResult(res as Record<string, unknown>);
  };

  return (
    <div className="flex flex-col gap-5">
      <Seo title={`${isFa ? 'زنجیرهٔ علمی زنده' : 'Live scientific chain'} | ${t.brand.name}`} path="/dashboard/live/chain" />
      <h1 className="text-2xl font-extrabold text-ink-1">
        {isFa ? 'زنجیرهٔ علمی زنده (RUSLE → SWAT → RothC → AquaCrop)' : 'Live scientific chain (RUSLE → SWAT → RothC → AquaCrop)'}
      </h1>

      <SectionCard title={isFa ? 'پارامترهای سایت' : 'Site parameters'}>
        <form onSubmit={run} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3" dir="ltr">Lat</span>
            <input type="number" step="0.01" value={lat} onChange={(e) => setLat(e.target.value)} className={inputCls} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3" dir="ltr">Lon</span>
            <input type="number" step="0.01" value={lon} onChange={(e) => setLon(e.target.value)} className={inputCls} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3">{isFa ? 'محصول' : 'Crop'}</span>
            <input type="text" value={crop} onChange={(e) => setCrop(e.target.value)} className={inputCls} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3">{isFa ? 'مساحت (هکتار)' : 'Area (ha)'}</span>
            <input type="number" step="0.5" value={areaHa} onChange={(e) => setAreaHa(e.target.value)} className={inputCls} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3">{isFa ? 'شیب (٪)' : 'Slope (%)'}</span>
            <input type="number" step="0.5" value={slope} onChange={(e) => setSlope(e.target.value)} className={inputCls} />
          </label>
          <button type="submit" className="col-span-full w-fit rounded-xl bg-leaf-500 px-6 py-2.5 text-xs font-extrabold text-night-950">
            {isFa ? 'اجرای زنجیرهٔ علمی' : 'Run scientific chain'}
          </button>
        </form>
      </SectionCard>

      <StateBanner state={chain.state} error={chain.error} retry={() => undefined} />

      {result ? (
        <div className="flex flex-col gap-4">
          {typeof result.data_sources === 'string' ? <Provenance source={result.data_sources} /> : null}
          {RESULT_SECTIONS.map((section) => {
            const value = result[section];
            if (!value || typeof value !== 'object') return null;
            return (
              <SectionCard key={section} title={section}>
                <KeyValues data={value as Record<string, unknown>} />
              </SectionCard>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
