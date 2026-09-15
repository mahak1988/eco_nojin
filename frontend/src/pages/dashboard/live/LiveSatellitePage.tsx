import { useState, type FormEvent } from 'react';
import Seo from '../../../components/ui/Seo';
import { satelliteApi } from '../../../lib/hydromaApi';
import { useLang } from '../../../i18n/LanguageContext';
import {
  KeyValues,
  Provenance,
  SectionCard,
  StateBanner,
  useLiveState,
} from '../../../components/dashboard/LivePanel';

/** A2 — live satellite data: ERA5 series + current weather for a coordinate. */
export default function LiveSatellitePage() {
  const { lang, t } = useLang();
  const isFa = lang === 'fa';
  const [lat, setLat] = useState('31.32');
  const [lon, setLon] = useState('50.70');
  const weather = useLiveState();
  const era5 = useLiveState();
  const [era5Result, setEra5Result] = useState<Record<string, unknown> | null>(null);
  const [weatherResult, setWeatherResult] = useState<Record<string, unknown> | null>(null);

  const inputCls =
    'w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-ink-1 focus:border-leaf-400/60 focus:outline-none';

  const runWeather = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const result = await weather.run(() => satelliteApi.weather(Number(lat), Number(lon), 7));
    if (result) setWeatherResult(result as Record<string, unknown>);
  };

  const runEra5 = async () => {
    const now = new Date();
    const end = now.toISOString().slice(0, 10);
    const start = new Date(now.getTime() - 30 * 86400000).toISOString().slice(0, 10);
    const result = await era5.run(() =>
      satelliteApi.era5Series({ lat: Number(lat), lon: Number(lon), start, end, variables: 'temperature_2m,precipitation' }),
    );
    if (result) setEra5Result(result as Record<string, unknown>);
  };

  return (
    <div className="flex flex-col gap-5">
      <Seo title={`${isFa ? 'پایش ماهواره‌ای زنده' : 'Live satellite monitoring'} | ${t.brand.name}`} path="/dashboard/live/satellite" />
      <h1 className="text-2xl font-extrabold text-ink-1">
        {isFa ? 'پایش ماهواره‌ای زنده' : 'Live satellite monitoring'}
      </h1>

      <SectionCard title={isFa ? 'مختصات زمین' : 'Field coordinates'}>
        <form onSubmit={runWeather} className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3" dir="ltr">Lat</span>
            <input type="number" step="0.01" value={lat} onChange={(e) => setLat(e.target.value)} className={inputCls} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold text-ink-3" dir="ltr">Lon</span>
            <input type="number" step="0.01" value={lon} onChange={(e) => setLon(e.target.value)} className={inputCls} />
          </label>
          <button type="submit" className="self-end rounded-xl bg-leaf-500 px-5 py-2.5 text-xs font-extrabold text-night-950">
            {isFa ? 'هواشناسی زنده' : 'Live weather'}
          </button>
        </form>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <button type="button" onClick={runEra5} className="rounded-xl bg-aqua-500/15 px-5 py-2.5 text-xs font-extrabold text-aqua-300 hover:bg-aqua-500/25">
            {isFa ? 'سری زمانی ERA5 (۳۰ روز)' : 'ERA5 series (30 days)'}
          </button>
        </div>
      </SectionCard>

      <SectionCard title={isFa ? 'هواشناسی فعلی' : 'Current weather'}>
        <StateBanner state={weather.state} error={weather.error} retry={runEra5} />
        {weatherResult ? <KeyValues data={weatherResult} /> : null}
      </SectionCard>

      <SectionCard title={isFa ? 'سری زمانی ERA5' : 'ERA5 time series'}>
        <StateBanner state={era5.state} error={era5.error} retry={runEra5} />
        {era5Result ? <KeyValues data={era5Result} /> : null}
        {era5Result && typeof era5Result.data_source === 'string' ? (
          <Provenance source={era5Result.data_source} />
        ) : null}
      </SectionCard>
    </div>
  );
}
