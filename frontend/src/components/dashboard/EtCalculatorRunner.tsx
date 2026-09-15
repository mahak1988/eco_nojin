/** Live runner for the et-calculator model (FAO-56 reference ET0).
 * Two live sections, both backed by real gateway endpoints:
 *  1. Real weather + ET0  -> GET /api/v1/satellite/weather
 *  2. Manual FAO-56       -> POST /api/v1/hydroma/climate/et-fao56/run
 *     (full Penman-Monteith when humidity/wind/radiation are provided,
 *      Hargreaves-Samani otherwise — the method used is reported). */

import { useState, type FormEvent } from 'react';
import { Droplets, FlaskConical } from 'lucide-react';
import { satelliteApi } from '../../lib/hydromaApi';
import { hydromaClimateApi } from '../../lib/hydromaTools';
import { useLang } from '../../i18n/LanguageContext';
import { KeyValues, SectionCard, StateBanner, useLiveState } from './LivePanel';

function extractEt0(data: Record<string, unknown>): { value: number; label: string } | null {
  const summary = data.summary;
  if (summary && typeof summary === 'object' && !Array.isArray(summary)) {
    const s = summary as Record<string, unknown>;
    for (const key of ['mean_et0_mm_day', 'total_et0_mm', 'et0', 'et0_mm', 'eto', 'eto_mm', 'reference_et0']) {
      const v = s[key];
      if (typeof v === 'number') return { value: v, label: key };
    }
    for (const [key, value] of Object.entries(s)) {
      if (key.toLowerCase().includes('et0') && typeof value === 'number') {
        return { value, label: key };
      }
    }
  }
  return null;
}

const inputCls =
  'w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-ink-1 focus:border-leaf-400/60 focus:outline-none';

/** A3 — live FAO-56 ET0 (et-calculator model). */
export default function EtCalculatorRunner() {
  const { lang } = useLang();
  const isFa = lang === 'fa';
  const weather = useLiveState();
  const manual = useLiveState();
  const [lat, setLat] = useState('35.70');
  const [lon, setLon] = useState('51.40');
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [manualValues, setManualValues] = useState<Record<string, string>>({
    tmin: '12', tmax: '28', rh_min: '30', rh_max: '80',
    wind_speed: '2', solar_radiation: '20', elevation: '1200', latitude: '35.7', doy: '180',
  });
  const [manualResult, setManualResult] = useState<Record<string, unknown> | null>(null);

  const runWeather = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setResult(null);
    const res = await weather.run(() => satelliteApi.weather(Number(lat), Number(lon), 7));
    if (res) setResult(res as Record<string, unknown>);
  };

  const runManual = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setManualResult(null);
    const res = await manual.run(() =>
      hydromaClimateApi.run('et-fao56', {
        ...manualValues,
        rh_min: manualValues.rh_min || undefined,
        rh_max: manualValues.rh_max || undefined,
        wind_speed: manualValues.wind_speed || undefined,
        solar_radiation: manualValues.solar_radiation || undefined,
      }),
    );
    if (res) setManualResult(res.result as Record<string, unknown>);
  };

  const et0 = result ? extractEt0(result) : null;
  const methodFa = manualResult?.method === 'penman_monteith' ? 'پنمن-مونتیث کامل' : 'هارگریوز-سامانی';
  const methodEn = manualResult?.method === 'penman_monteith' ? 'full Penman-Monteith' : 'Hargreaves-Samani';

  return (
    <div className="flex flex-col gap-4">
      <SectionCard
        title={
          <span className="inline-flex items-center gap-2">
            <Droplets className="h-4 w-4 text-aqua-400" aria-hidden />
            {isFa ? 'ET0 از هواشناسی واقعی' : 'ET0 from real weather'}
          </span>
        }
      >
        <form onSubmit={runWeather} className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
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
            disabled={weather.state === 'loading'}
            className="self-end rounded-xl bg-leaf-500 px-5 py-2.5 text-xs font-extrabold text-night-950 disabled:opacity-60"
          >
            {weather.state === 'loading' ? (isFa ? 'در حال دریافت…' : 'Fetching…') : isFa ? 'دریافت ET0' : 'Fetch ET0'}
          </button>
        </form>
        <div className="mt-3">
          <StateBanner state={weather.state} error={weather.error} retry={() => undefined} />
        </div>

        {et0 ? (
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-2xl font-extrabold text-aqua-300" dir="ltr">{et0.value.toFixed(2)}</p>
              <p className="text-[11px] text-ink-3">{isFa ? 'ET0 (mm/day)' : 'ET0 (mm/day)'}</p>
            </div>
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-sm font-extrabold text-ink-1" dir="ltr">{String(result?.source ?? '—')}</p>
              <p className="text-[11px] text-ink-3">{isFa ? 'منبع داده' : 'Data source'}</p>
            </div>
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-sm font-extrabold text-ink-1" dir="ltr">{String(result?.days ?? 0)}</p>
              <p className="text-[11px] text-ink-3">{isFa ? 'روز' : 'days'}</p>
            </div>
          </div>
        ) : null}

        {result ? (
          <details className="mt-3">
            <summary className="cursor-pointer text-[11px] font-bold text-ink-3 hover:text-ink-2">
              {isFa ? 'پاسخ کامل سرویس' : 'Full service response'}
            </summary>
            <div className="mt-2">
              <KeyValues data={result} />
            </div>
          </details>
        ) : null}
      </SectionCard>

      <SectionCard
        title={
          <span className="inline-flex items-center gap-2">
            <FlaskConical className="h-4 w-4 text-leaf-400" aria-hidden />
            {isFa ? 'FAO-56 دستی (دادههای اقلیمی خودتان)' : 'Manual FAO-56 (your own climate data)'}
          </span>
        }
      >
        <form onSubmit={runManual} className="grid gap-3 sm:grid-cols-3">
          {[
            ['tmin', 'T min', 'C'],
            ['tmax', 'T max', 'C'],
            ['rh_min', 'RH min', '%'],
            ['rh_max', 'RH max', '%'],
            ['wind_speed', 'Wind', 'm/s'],
            ['solar_radiation', 'Solar', 'MJ/m²'],
            ['elevation', 'Elevation', 'm'],
            ['latitude', 'Latitude', 'deg'],
            ['doy', 'Day of year', ''],
          ].map(([name, label, unit]) => (
            <label key={name} className="flex flex-col gap-1">
              <span className="text-[11px] font-bold text-ink-3" dir="ltr">
                {label}
                {unit ? <span className="text-ink-4"> ({unit})</span> : null}
              </span>
              <input
                type="number"
                step="any"
                dir="ltr"
                value={manualValues[name] ?? ''}
                onChange={(e) => setManualValues((prev) => ({ ...prev, [name]: e.target.value }))}
                className={inputCls}
              />
            </label>
          ))}
          <button
            type="submit"
            disabled={manual.state === 'loading'}
            className="self-end rounded-xl bg-leaf-500 px-5 py-2.5 text-xs font-extrabold text-night-950 disabled:opacity-60"
          >
            {manual.state === 'loading' ? (isFa ? 'در حال اجرا…' : 'Running…') : isFa ? 'محاسبه ET0' : 'Compute ET0'}
          </button>
        </form>
        <p className="mt-2 text-[11px] leading-5 text-ink-3">
          {isFa
            ? 'RH/باد/تابش اختیاریاند — اگر خالی بمانند موتور به هارگریوز-سامانی برمیگردد و روش استفادهشده صادقانه گزارش میشود.'
            : 'RH/wind/radiation are optional — when empty the engine falls back to Hargreaves-Samani and reports the method used.'}
        </p>
        <div className="mt-3">
          <StateBanner state={manual.state} error={manual.error} retry={() => undefined} />
        </div>

        {manualResult ? (
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-2xl font-extrabold text-leaf-300" dir="ltr">
                {typeof manualResult.et0_mm_day === 'number' ? manualResult.et0_mm_day.toFixed(2) : '—'}
              </p>
              <p className="text-[11px] text-ink-3">{isFa ? 'ET0 (mm/day)' : 'ET0 (mm/day)'}</p>
            </div>
            <div className="rounded-xl bg-black/20 p-4 text-center">
              <p className="text-sm font-extrabold text-ink-1">{isFa ? methodFa : methodEn}</p>
              <p className="text-[11px] text-ink-3">{isFa ? 'روش محاسبه' : 'Method used'}</p>
            </div>
          </div>
        ) : null}
      </SectionCard>
    </div>
  );
}
