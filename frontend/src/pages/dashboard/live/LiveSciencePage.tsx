import { useState, type FormEvent } from 'react';
import Seo from '../../../components/ui/Seo';
import { chainApi, type ChainRequest } from '../../../lib/hydromaApi';
import { useLang } from '../../../i18n/LanguageContext';
import { KeyValues, Provenance, SectionCard, StateBanner, useLiveState } from '../../../components/dashboard/LivePanel';

const RESULT_SECTIONS: { key: string; titleFa: string; titleEn: string }[] = [
  { key: 'erosion', titleFa: 'فرسایش (RUSLE)', titleEn: 'Erosion (RUSLE)' },
  { key: 'swat', titleFa: 'آبخیز (SWAT+)', titleEn: 'Watershed (SWAT+)' },
  { key: 'water', titleFa: 'آب و آبیاری', titleEn: 'Water & irrigation' },
  { key: 'flood', titleFa: 'سیلاب (HEC-RAS)', titleEn: 'Flood (HEC-RAS)' },
  { key: 'optimization', titleFa: 'بهینه‌سازی سناریو', titleEn: 'Scenario optimization' },
  { key: 'rothc', titleFa: 'کربن خاک (RothC)', titleEn: 'Soil carbon (RothC)' },
  { key: 'aquacrop', titleFa: 'عملکرد محصول (AquaCrop)', titleEn: 'Crop yield (AquaCrop)' },
  { key: 'calibration', titleFa: 'کالیبراسیون', titleEn: 'Calibration' },
];

/** B — science-live: the full engine chain with per-model outputs and the
 * provenance discipline (real / simulated / no_data) shown on every block. */
export default function LiveSciencePage() {
  const { lang, t } = useLang();
  const isFa = lang === 'fa';
  const [lat, setLat] = useState('31.32');
  const [lon, setLon] = useState('50.70');
  const [crop, setCrop] = useState('wheat');
  const [slope, setSlope] = useState('3');
  const [practice, setPractice] = useState('none');
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
      practice,
      optimize: true,
    };
    const res = await chain.run(() => chainApi.motors(body));
    if (res) setResult(res as Record<string, unknown>);
  };

  const dataSources = result?.data_sources as Record<string, unknown> | undefined;
  const inputs = result?.inputs as Record<string, unknown> | undefined;

  return (
    <div className="flex flex-col gap-5">
      <Seo title={`${isFa ? 'زنجیرهٔ علمی (زنده)' : 'Scientific chain (live)'} | ${t.brand.name}`} path="/dashboard/science-live" />
      <h1 className="text-2xl font-extrabold text-ink-1">
        {isFa ? 'زنجیرهٔ علمی زنده — RUSLE → SWAT → RothC → AquaCrop' : 'Live scientific chain — RUSLE → SWAT → RothC → AquaCrop'}
      </h1>
      <p className="max-w-3xl text-xs leading-6 text-ink-3">
        {isFa
          ? 'این صفحه زنجیرهٔ کامل موتور را اجرا می‌کند؛ هر خروجی برچسب منشأ دارد (واقعی / شبیه‌سازی / بدون داده) — همان انضباط MRV. اجرا نیازمند ورود است.'
          : 'This page runs the full engine chain; every output carries a provenance badge (real / simulated / no_data) — the MRV discipline. Running requires login.'}
      </p>

      <SectionCard title={isFa ? 'پارامترهای سایت' : 'Site parameters'}>
        <form onSubmit={run} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3" dir="ltr">Lat</span>
            <input type="number" step="0.01" value={lat} onChange={(e) => setLat(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3" dir="ltr">Lon</span>
            <input type="number" step="0.01" value={lon} onChange={(e) => setLon(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'محصول' : 'Crop'}</span>
            <input type="text" value={crop} onChange={(e) => setCrop(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'شیب ٪' : 'Slope %'}</span>
            <input type="number" step="0.5" value={slope} onChange={(e) => setSlope(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'اقدام' : 'Practice'}</span>
            <input type="text" value={practice} onChange={(e) => setPractice(e.target.value)} className={inputCls} /></label>
          <button type="submit" className="self-end rounded-xl bg-leaf-500 px-5 py-2.5 text-xs font-extrabold text-night-950">
            {isFa ? 'اجرای زنجیره' : 'Run chain'}
          </button>
        </form>
        <div className="mt-3">
          <StateBanner state={chain.state} error={chain.error} kind={chain.kind} retry={() => undefined} />
        </div>
      </SectionCard>

      {!result && chain.state === 'idle' ? (
        <p className="text-[11px] text-ink-3">
          {isFa ? 'برای دیدن خروجی هر مدل، زنجیره را اجرا کنید.' : 'Run the chain to see per-model outputs.'}
        </p>
      ) : null}

      {inputs ? (
        <SectionCard title={isFa ? 'ورودی‌های محاسبه‌شده (واقعی)' : 'Computed inputs (real)'} badge={<Provenance source="real" />}>
          <KeyValues data={inputs} />
        </SectionCard>
      ) : null}

      {result
        ? RESULT_SECTIONS.map((section) => {
            const value = result[section.key];
            if (!value || typeof value !== 'object') {
              return (
                <SectionCard key={section.key} title={isFa ? section.titleFa : section.titleEn} badge={<Provenance source="no_data" />}>
                  <p className="text-[11px] text-ink-3">
                    {isFa ? 'این حلقه در پاسخ زنجیره حاضر نشد.' : 'This link was absent from the chain response.'}
                  </p>
                </SectionCard>
              );
            }
            const block = value as Record<string, unknown>;
            const source =
              (typeof block.data_source === 'string' && block.data_source) ||
              (typeof block.status === 'string' && block.status === 'completed' ? 'real' : undefined) ||
              (dataSources && typeof dataSources[section.key] === 'string' ? String(dataSources[section.key]) : undefined);
            return (
              <SectionCard key={section.key} title={isFa ? section.titleFa : section.titleEn} badge={<Provenance source={source} />}>
                <KeyValues data={block} />
              </SectionCard>
            );
          })
        : null}

    </div>
  );
}
