import { useState, type FormEvent } from 'react';
import Seo from '../../../components/ui/Seo';
import { soilApi } from '../../../lib/hydromaApi';
import { useLang } from '../../../i18n/LanguageContext';
import { KeyValues, SectionCard, StateBanner, useLiveState } from '../../../components/dashboard/LivePanel';

/** A6 — live soil analysis + RUSLE erosion (server-side). */
export default function LiveSoilPage() {
  const { lang, t } = useLang();
  const isFa = lang === 'fa';
  const analyze = useLiveState();
  const erosion = useLiveState();
  const [analyzeResult, setAnalyzeResult] = useState<Record<string, unknown> | null>(null);
  const [erosionResult, setErosionResult] = useState<Record<string, unknown> | null>(null);

  // analyze form
  const [ph, setPh] = useState('7.0');
  const [om, setOm] = useState('1.5');
  const [clay, setClay] = useState('25');
  const [sand, setSand] = useState('40');
  const [silt, setSilt] = useState('35');

  // erosion form
  const [slopeLen, setSlopeLen] = useState('100');
  const [slopePct, setSlopePct] = useState('3');
  const [rain, setRain] = useState('450');
  const [texture, setTexture] = useState('loam');
  const [cFactor, setCFactor] = useState('0.2');
  const [pFactor, setPFactor] = useState('1.0');

  const inputCls =
    'w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-ink-1 focus:border-leaf-400/60 focus:outline-none';

  const runAnalyze = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const res = await analyze.run(() =>
      soilApi.analyze({
        pH: Number(ph),
        organic_matter: Number(om),
        clay: Number(clay),
        sand: Number(sand),
        silt: Number(silt),
        language: lang,
      }),
    );
    if (res) setAnalyzeResult(res as Record<string, unknown>);
  };

  const runErosion = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const res = await erosion.run(() =>
      soilApi.erosion({
        slope_length_m: Number(slopeLen),
        slope_percent: Number(slopePct),
        annual_rainfall_mm: Number(rain),
        texture,
        c_factor: Number(cFactor),
        p_factor: Number(pFactor),
      }),
    );
    if (res) setErosionResult(res as Record<string, unknown>);
  };

  return (
    <div className="flex flex-col gap-5">
      <Seo title={`${isFa ? 'خاک زنده' : 'Live soil'} | ${t.brand.name}`} path="/dashboard/live/soil" />
      <h1 className="text-2xl font-extrabold text-ink-1">{isFa ? 'خاک زنده' : 'Live soil'}</h1>

      <SectionCard title={isFa ? 'تحلیل خاک (pH/بافت/مادهٔ آلی)' : 'Soil analysis (pH/texture/OM)'}>
        <form onSubmit={runAnalyze} className="grid gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">pH</span>
            <input type="number" step="0.1" value={ph} onChange={(e) => setPh(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'مادهٔ آلی ٪' : 'OM %'}</span>
            <input type="number" step="0.1" value={om} onChange={(e) => setOm(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'رس ٪' : 'Clay %'}</span>
            <input type="number" step="1" value={clay} onChange={(e) => setClay(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'ماسه ٪' : 'Sand %'}</span>
            <input type="number" step="1" value={sand} onChange={(e) => setSand(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'سیلت ٪' : 'Silt %'}</span>
            <input type="number" step="1" value={silt} onChange={(e) => setSilt(e.target.value)} className={inputCls} /></label>
          <button type="submit" className="col-span-full w-fit rounded-xl bg-leaf-500 px-6 py-2.5 text-xs font-extrabold text-night-950">
            {isFa ? 'تحلیل خاک' : 'Analyze soil'}
          </button>
        </form>
        <div className="mt-3"><StateBanner state={analyze.state} error={analyze.error} retry={() => undefined} /></div>
        {analyzeResult ? <KeyValues data={analyzeResult} /> : null}
      </SectionCard>

      <SectionCard title={isFa ? 'فرسایش RUSLE (سمت سرور)' : 'RUSLE erosion (server-side)'}>
        <form onSubmit={runErosion} className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'طول شیب (m)' : 'Slope length'}</span>
            <input type="number" step="1" value={slopeLen} onChange={(e) => setSlopeLen(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'شیب ٪' : 'Slope %'}</span>
            <input type="number" step="0.5" value={slopePct} onChange={(e) => setSlopePct(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'بارش (mm)' : 'Rain (mm)'}</span>
            <input type="number" step="1" value={rain} onChange={(e) => setRain(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'بافت' : 'Texture'}</span>
            <input type="text" value={texture} onChange={(e) => setTexture(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3" dir="ltr">C</span>
            <input type="number" step="0.05" value={cFactor} onChange={(e) => setCFactor(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3" dir="ltr">P</span>
            <input type="number" step="0.1" value={pFactor} onChange={(e) => setPFactor(e.target.value)} className={inputCls} /></label>
          <button type="submit" className="col-span-full w-fit rounded-xl bg-leaf-500 px-6 py-2.5 text-xs font-extrabold text-night-950">
            {isFa ? 'محاسبهٔ فرسایش' : 'Compute erosion'}
          </button>
        </form>
        <div className="mt-3"><StateBanner state={erosion.state} error={erosion.error} retry={() => undefined} /></div>
        {erosionResult ? <KeyValues data={erosionResult} /> : null}
      </SectionCard>
    </div>
  );
}
