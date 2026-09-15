import { useMemo, useState, type FormEvent } from 'react';
import Seo from '../../../components/ui/Seo';
import { satelliteApi } from '../../../lib/hydromaApi';
import { useLang } from '../../../i18n/LanguageContext';
import { KeyValues, SectionCard, StateBanner, useLiveState } from '../../../components/dashboard/LivePanel';

/** FAO-56 Hargreaves-Samani ET0 (Allen et al. 1998) — pure formula. */
function hargreavesEt0(latDeg: number, tmaxC: number, tminC: number, dayOfYear: number): number {
  const tmean = (tmaxC + tminC) / 2;
  const phi = (latDeg * Math.PI) / 180;
  const dr = 1 + 0.033 * Math.cos((2 * Math.PI * dayOfYear) / 365);
  const delta = 0.409 * Math.sin((2 * Math.PI * dayOfYear) / 365 - 1.39);
  const ws = Math.acos(-Math.tan(phi) * Math.tan(delta));
  const ra = (24 * 60 / Math.PI) * 0.082 * dr * (ws * Math.sin(phi) * Math.sin(delta) + Math.cos(phi) * Math.cos(delta) * Math.sin(ws));
  return 0.0023 * ra * (tmean + 17.8) * Math.sqrt(Math.max(0, tmaxC - tminC));
}

/** A3 — live ET0: real weather (satellite/weather) + Hargreaves-Samani. */
export default function LiveEt0Page() {
  const { lang, t } = useLang();
  const isFa = lang === 'fa';
  const weather = useLiveState();
  const [lat, setLat] = useState('31.32');
  const [lon, setLon] = useState('50.70');
  const [weatherResult, setWeatherResult] = useState<Record<string, unknown> | null>(null);

  const inputCls =
    'w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-ink-1 focus:border-leaf-400/60 focus:outline-none';

  const run = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const res = await weather.run(() => satelliteApi.weather(Number(lat), Number(lon), 7));
    if (res) setWeatherResult(res as Record<string, unknown>);
  };

  const et0 = useMemo(() => {
    if (!weatherResult) return null;
    const pick = (...keys: string[]): number | null => {
      for (const key of keys) {
        const value = weatherResult[key];
        if (typeof value === 'number') return value;
        if (Array.isArray(value) && typeof value[0] === 'number') return value[0];
      }
      return null;
    };
    const tmax = pick('tmax', 'temperature_max', 'temperature_2m_max');
    const tmin = pick('tmin', 'temperature_min', 'temperature_2m_min');
    if (tmax === null || tmin === null) return null;
    const dayOfYear = Math.floor((Date.now() - new Date(new Date().getFullYear(), 0, 0).getTime()) / 86400000);
    return { tmax, tmin, et0: hargreavesEt0(Number(lat), tmax, tmin, dayOfYear) };
  }, [weatherResult, lat]);

  return (
    <div className="flex flex-col gap-5">
      <Seo title={`${isFa ? 'تبخیر-تعرق زنده' : 'Live ET0'} | ${t.brand.name}`} path="/dashboard/live/et0" />
      <h1 className="text-2xl font-extrabold text-ink-1">{isFa ? 'تبخیر-تعرق مرجع (ET0) زنده' : 'Live reference ET0'}</h1>

      <SectionCard title={isFa ? 'مختصات + هواشناسی واقعی' : 'Coordinates + real weather'}>
        <form onSubmit={run} className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3" dir="ltr">Lat</span>
            <input type="number" step="0.01" value={lat} onChange={(e) => setLat(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3" dir="ltr">Lon</span>
            <input type="number" step="0.01" value={lon} onChange={(e) => setLon(e.target.value)} className={inputCls} /></label>
          <button type="submit" className="self-end rounded-xl bg-leaf-500 px-5 py-2.5 text-xs font-extrabold text-night-950">
            {isFa ? 'دریافت هواشناسی' : 'Fetch weather'}
          </button>
        </form>
        <div className="mt-3"><StateBanner state={weather.state} error={weather.error} retry={() => undefined} /></div>
      </SectionCard>

      {et0 ? (
        <SectionCard title={isFa ? 'ET0 محاسبه‌شده (Hargreaves-Samani)' : 'Computed ET0 (Hargreaves-Samani)'}>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-2xl font-extrabold text-aqua-300" dir="ltr">{et0.et0.toFixed(2)}</p>
              <p className="text-[11px] text-ink-3">{isFa ? 'ET0 (mm/day)' : 'ET0 (mm/day)'}</p>
            </div>
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-2xl font-extrabold text-ink-1" dir="ltr">{et0.tmax.toFixed(1)}°C</p>
              <p className="text-[11px] text-ink-3">Tmax</p>
            </div>
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-2xl font-extrabold text-ink-1" dir="ltr">{et0.tmin.toFixed(1)}°C</p>
              <p className="text-[11px] text-ink-3">Tmin</p>
            </div>
          </div>
          <p className="mt-3 text-[11px] text-ink-3">
            {isFa
              ? 'محاسبه از دمای واقعی ERA5 انجام می‌شود؛ پنمن‌-مونتیث کامل با داده‌های دستی خودتان روی صفحهٔ مدل ET0 در دسترس است.'
              : 'Computed from real ERA5 temperature; full Penman-Monteith with your own climate data is on the ET0 model page.'}
          </p>
        </SectionCard>
      ) : null}

      {weatherResult ? (
        <SectionCard title={isFa ? 'پاسخ خام هواشناسی' : 'Raw weather response'}>
          <KeyValues data={weatherResult} />
        </SectionCard>
      ) : null}
    </div>
  );
}
