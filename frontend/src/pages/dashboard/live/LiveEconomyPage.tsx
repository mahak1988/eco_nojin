import { useState, type FormEvent } from 'react';
import Seo from '../../../components/ui/Seo';
import { chainApi, motorsApi, type ManualSiteRun } from '../../../lib/hydromaApi';
import { useLang } from '../../../i18n/LanguageContext';
import { KeyValues, Provenance, SectionCard, StateBanner, useLiveState } from '../../../components/dashboard/LivePanel';

/** B — economy: NPV/ROI from the admin-only economy motor, with an honest
 * RBAC path and a fallback to the public scientific chain's optimization. */
export default function LiveEconomyPage() {
  const { lang, t } = useLang();
  const isFa = lang === 'fa';
  const [siteId, setSiteId] = useState('demo-site-01');
  const [crop, setCrop] = useState('wheat');
  const [lat, setLat] = useState('31.32');
  const [lon, setLon] = useState('50.70');
  const economy = useLiveState();
  const chain = useLiveState();
  const [economyResult, setEconomyResult] = useState<Record<string, unknown> | null>(null);
  const [chainResult, setChainResult] = useState<Record<string, unknown> | null>(null);

  const inputCls =
    'w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-ink-1 focus:border-leaf-400/60 focus:outline-none';

  const runEconomy = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const body: ManualSiteRun = { site_id: siteId.trim(), crop_name: crop };
    const res = await economy.run(() => motorsApi.siteRun('economy', body));
    if (res) setEconomyResult(res as Record<string, unknown>);
  };

  const runChain = async () => {
    const res = await chain.run(() =>
      chainApi.motors({ lat: Number(lat), lon: Number(lon), crop, slope_pct: 3, optimize: true }),
    );
    if (res) setChainResult(res as Record<string, unknown>);
  };

  const optimization = chainResult?.optimization as Record<string, unknown> | undefined;

  return (
    <div className="flex flex-col gap-5">
      <Seo title={`${isFa ? 'اقتصاد (NPV/ROI)' : 'Economy (NPV/ROI)'} | ${t.brand.name}`} path="/dashboard/economy" />
      <h1 className="text-2xl font-extrabold text-ink-1">{isFa ? 'اقتصاد پروژه — NPV و ROI' : 'Project economy — NPV & ROI'}</h1>

      <SectionCard title={isFa ? 'موتور اقتصاد (نیازمند نقش admin)' : 'Economy motor (requires admin role)'}>
        <form onSubmit={runEconomy} className="grid gap-3 sm:grid-cols-[1fr_1fr_1fr_auto]">
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'شناسهٔ سایت' : 'Site id'}</span>
            <input type="text" dir="ltr" value={siteId} onChange={(e) => setSiteId(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'محصول' : 'Crop'}</span>
            <input type="text" value={crop} onChange={(e) => setCrop(e.target.value)} className={inputCls} /></label>
          <span className="hidden sm:block" />
          <button type="submit" className="self-end rounded-xl bg-leaf-500 px-5 py-2.5 text-xs font-extrabold text-night-950">
            {isFa ? 'اجرای موتور اقتصاد' : 'Run economy motor'}
          </button>
        </form>
        <div className="mt-3">
          <StateBanner state={economy.state} error={economy.error} kind={economy.kind} retry={() => undefined} />
        </div>
        {economyResult ? <KeyValues data={economyResult} /> : null}
        <p className="mt-3 text-[11px] leading-6 text-ink-3">
          {isFa
            ? 'این موتور در نسخهٔ فعلی فقط برای نقش admin باز است (خروجی واقعی NPV/IRR/بازگشت). کاربران farmer می‌توانند از مسیر جایگزین زیر استفاده کنند.'
            : 'This motor is admin-only in the current release (real NPV/IRR/payback output). Farmer accounts can use the alternative path below.'}
        </p>
      </SectionCard>

      <SectionCard title={isFa ? 'مسیر جایگزین: بهینه‌سازی زنجیرهٔ علمی (برای همه)' : 'Alternative: scientific-chain optimization (all roles)'}>
        <form onSubmit={(e) => { e.preventDefault(); runChain(); }} className="grid gap-3 sm:grid-cols-[1fr_1fr_1fr_auto]">
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3" dir="ltr">Lat</span>
            <input type="number" step="0.01" value={lat} onChange={(e) => setLat(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3" dir="ltr">Lon</span>
            <input type="number" step="0.01" value={lon} onChange={(e) => setLon(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3">{isFa ? 'محصول' : 'Crop'}</span>
            <input type="text" value={crop} onChange={(e) => setCrop(e.target.value)} className={inputCls} /></label>
          <button type="submit" className="self-end rounded-xl bg-aqua-500/20 px-5 py-2.5 text-xs font-extrabold text-aqua-300 hover:bg-aqua-500/30">
            {isFa ? 'اجرای بهینه‌سازی' : 'Run optimization'}
          </button>
        </form>
        <div className="mt-3">
          <StateBanner state={chain.state} error={chain.error} kind={chain.kind} retry={() => undefined} />
        </div>
        {optimization ? (
          <div className="mt-3">
            <div className="mb-2 flex items-center gap-2">
              <h3 className="text-xs font-extrabold text-ink-1">{isFa ? 'خروجی بهینه‌سازی' : 'Optimization output'}</h3>
              <Provenance source="simulated" />
            </div>
            <KeyValues data={optimization} />
          </div>
        ) : null}
      </SectionCard>
    </div>
  );
}
