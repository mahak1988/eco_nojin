import { useState, type FormEvent } from 'react';
import Seo from '../../../components/ui/Seo';
import { carbonApi } from '../../../lib/hydromaApi';
import { useLang } from '../../../i18n/LanguageContext';
import { KeyValues, SectionCard, StateBanner, useLiveState } from '../../../components/dashboard/LivePanel';

/** A7 — live carbon: MRV carbon budget + RothC-style soil-carbon (server). */
export default function LiveCarbonPage() {
  const { lang, t } = useLang();
  const isFa = lang === 'fa';
  const budget = useLiveState();
  const soilC = useLiveState();
  const [budgetResult, setBudgetResult] = useState<Record<string, unknown> | null>(null);
  const [soilCResult, setSoilCResult] = useState<Record<string, unknown> | null>(null);

  const [lat, setLat] = useState('31.32');
  const [lon, setLon] = useState('50.70');
  const [areaHa, setAreaHa] = useState('10');
  const [crop, setCrop] = useState('wheat');
  const [practice, setPractice] = useState('agroforestry');

  const [initC, setInitC] = useState('30');
  const [annualInput, setAnnualInput] = useState('4');
  const [clay, setClay] = useState('25');
  const [temp, setTemp] = useState('18');
  const [rainfall, setRainfall] = useState('450');
  const [years, setYears] = useState('20');

  const inputCls =
    'w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-ink-1 focus:border-leaf-400/60 focus:outline-none';

  const runBudget = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const res = await budget.run(() =>
      carbonApi.budget({
        lat: Number(lat),
        lon: Number(lon),
        area_ha: Number(areaHa),
        crop,
        practice,
        methodology: 'ipcc-tier1',
      }),
    );
    if (res) setBudgetResult(res as Record<string, unknown>);
  };

  const runSoilC = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const res = await soilC.run(() =>
      carbonApi.soilCarbon({
        initial_C_tha: Number(initC),
        annual_input_tha: Number(annualInput),
        clay_pct: Number(clay),
        temperature_C: Number(temp),
        rainfall_mm: Number(rainfall),
        years: Number(years),
      }),
    );
    if (res) setSoilCResult(res as Record<string, unknown>);
  };

  return (
    <div className="flex flex-col gap-5">
      <Seo title={`${isFa ? 'کربن زنده' : 'Live carbon'} | ${t.brand.name}`} path="/dashboard/live/carbon" />
      <h1 className="text-2xl font-extrabold text-ink-1">{isFa ? 'کربن و MRV زنده' : 'Live carbon & MRV'}</h1>

      <SectionCard title={isFa ? 'بودجهٔ کربن (MRV)' : 'Carbon budget (MRV)'}>
        <form onSubmit={runBudget} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3" dir="ltr">Lat</span>
            <input type="number" step="0.01" value={lat} onChange={(e) => setLat(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3" dir="ltr">Lon</span>
            <input type="number" step="0.01" value={lon} onChange={(e) => setLon(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'مساحت' : 'Area (ha)'}</span>
            <input type="number" step="0.5" value={areaHa} onChange={(e) => setAreaHa(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'محصول' : 'Crop'}</span>
            <input type="text" value={crop} onChange={(e) => setCrop(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'اقدام' : 'Practice'}</span>
            <input type="text" value={practice} onChange={(e) => setPractice(e.target.value)} className={inputCls} /></label>
          <button type="submit" className="col-span-full w-fit rounded-xl bg-leaf-500 px-6 py-2.5 text-xs font-extrabold text-night-950">
            {isFa ? 'محاسبهٔ بودجهٔ کربن' : 'Compute carbon budget'}
          </button>
        </form>
        <div className="mt-3"><StateBanner state={budget.state} error={budget.error} retry={() => undefined} /></div>
        {budgetResult ? <KeyValues data={budgetResult} /> : null}
      </SectionCard>

      <SectionCard title={isFa ? 'کربن آلی خاک (مدل)' : 'Soil organic carbon (model)'}>
        <form onSubmit={runSoilC} className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'C اولیه' : 'Initial C (t/ha)'}</span>
            <input type="number" step="1" value={initC} onChange={(e) => setInitC(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'ورودی سالانه' : 'Input (t/ha/yr)'}</span>
            <input type="number" step="0.5" value={annualInput} onChange={(e) => setAnnualInput(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'رس ٪' : 'Clay %'}</span>
            <input type="number" step="1" value={clay} onChange={(e) => setClay(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'دما °C' : 'Temp °C'}</span>
            <input type="number" step="1" value={temp} onChange={(e) => setTemp(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'بارش' : 'Rain (mm)'}</span>
            <input type="number" step="1" value={rainfall} onChange={(e) => setRainfall(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'سال' : 'Years'}</span>
            <input type="number" step="1" value={years} onChange={(e) => setYears(e.target.value)} className={inputCls} /></label>
          <button type="submit" className="col-span-full w-fit rounded-xl bg-leaf-500 px-6 py-2.5 text-xs font-extrabold text-night-950">
            {isFa ? 'شبیه‌سازی کربن خاک' : 'Simulate soil carbon'}
          </button>
        </form>
        <div className="mt-3"><StateBanner state={soilC.state} error={soilC.error} retry={() => undefined} /></div>
        {soilCResult ? <KeyValues data={soilCResult} /> : null}
      </SectionCard>
    </div>
  );
}
