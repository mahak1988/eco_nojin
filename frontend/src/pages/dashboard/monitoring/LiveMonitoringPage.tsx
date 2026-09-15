import { useState, type FormEvent } from 'react';
import Seo from '../../../components/ui/Seo';
import { satelliteApi, soilApi } from '../../../lib/hydromaApi';
import { useLang } from '../../../i18n/LanguageContext';
import {
  KeyValues,
  Provenance,
  SectionCard,
  StateBanner,
  useLiveState,
} from '../../../components/dashboard/LivePanel';

/** B — monitoring: real satellite/ERA5 evidence for a field, replacing the
 * conceptual gallery with data-backed cards and honest provenance badges. */

function extractNumber(source: Record<string, unknown> | null, keys: string[]): number | null {
  if (!source) return null;
  for (const key of keys) {
    const value = source[key];
    if (typeof value === 'number') return value;
    if (source.summary && typeof source.summary === 'object') {
      const nested = (source.summary as Record<string, unknown>)[key];
      if (typeof nested === 'number') return nested;
    }
  }
  return null;
}

export default function LiveMonitoringPage() {
  const { lang, t } = useLang();
  const isFa = lang === 'fa';
  const [lat, setLat] = useState('31.32');
  const [lon, setLon] = useState('50.70');
  const scene = useLiveState();
  const weather = useLiveState();
  const erosion = useLiveState();
  const [sceneResult, setSceneResult] = useState<Record<string, unknown> | null>(null);
  const [weatherResult, setWeatherResult] = useState<Record<string, unknown> | null>(null);
  const [erosionResult, setErosionResult] = useState<Record<string, unknown> | null>(null);

  const inputCls =
    'w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-ink-1 focus:border-leaf-400/60 focus:outline-none';

  const runAll = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const coords = { lat: Number(lat), lon: Number(lon) };
    const [sceneRes, weatherRes, erosionRes] = await Promise.all([
      scene.run(() => satelliteApi.analyze(coords.lat, coords.lon)),
      weather.run(() => satelliteApi.weather(coords.lat, coords.lon, 7)),
      erosion.run(() =>
        soilApi.erosion({
          slope_length_m: 100,
          slope_percent: 3,
          annual_rainfall_mm: 450,
          texture: 'loam',
          c_factor: 0.2,
          p_factor: 1.0,
        }),
      ),
    ]);
    if (sceneRes) setSceneResult(sceneRes as Record<string, unknown>);
    if (weatherRes) setWeatherResult(weatherRes as Record<string, unknown>);
    if (erosionRes) setErosionResult(erosionRes as Record<string, unknown>);
  };

  const ndvi = extractNumber(sceneResult, ['ndvi']);
  const et0 = extractNumber(weatherResult, ['total_et0_mm', 'et0_mm']);
  const rain = extractNumber(weatherResult, ['total_precipitation_mm', 'precipitation_mm']);
  const soilLoss = extractNumber(erosionResult, ['annual_soil_loss_t_per_ha', 'soil_loss_t_ha']);

  const gallery = [
    {
      key: 'ndvi',
      title: isFa ? 'شاخص پوشش گیاهی (NDVI)' : 'Vegetation index (NDVI)',
      value: ndvi !== null ? ndvi.toFixed(3) : isFa ? 'در دسترس نیست' : 'unavailable',
      source: sceneResult?.data_source ? String(sceneResult.data_source) : 'no_data',
      hint: isFa
        ? 'صحنهٔ ماهواره‌ای نیازمند اعتبارنامهٔ CDSE است؛ با تنظیم اعتبار، مقدار واقعی اینجا می‌آید.'
        : 'Scene analysis needs CDSE credentials; the real value appears here once configured.',
    },
    {
      key: 'et0',
      title: 'ET0 — ' + (isFa ? '۷ روز' : '7 days'),
      value: et0 !== null ? `${et0.toFixed(2)} mm` : '—',
      source: weatherResult ? 'real' : 'no_data',
      hint: weatherResult ? (isFa ? 'از Open-Meteo/ERA5 — دادهٔ واقعی' : 'From Open-Meteo/ERA5 — real data') : '',
    },
    {
      key: 'rain',
      title: isFa ? 'بارش تجمعی' : 'Cumulative rainfall',
      value: rain !== null ? `${rain.toFixed(1)} mm` : '—',
      source: weatherResult ? 'real' : 'no_data',
      hint: weatherResult ? (isFa ? 'از Open-Meteo/ERA5' : 'From Open-Meteo/ERA5') : '',
    },
    {
      key: 'erosion',
      title: isFa ? 'تلفات خاک (RUSLE)' : 'Soil loss (RUSLE)',
      value: soilLoss !== null ? `${soilLoss.toFixed(2)} t/ha/yr` : '—',
      source: erosionResult ? 'real' : 'no_data',
      hint: erosionResult ? (isFa ? 'محاسبهٔ سرور از موتور روسل' : 'Server-side RUSLE engine') : '',
    },
  ];

  return (
    <div className="flex flex-col gap-5">
      <Seo title={`${isFa ? 'پایش زمین (زنده)' : 'Field monitoring (live)'} | ${t.brand.name}`} path="/dashboard/monitoring" />
      <h1 className="text-2xl font-extrabold text-ink-1">{isFa ? 'پایش زمین (زنده)' : 'Field monitoring (live)'}</h1>

      <SectionCard title={isFa ? 'مختصات زمین و اجرای پایش' : 'Field coordinates & monitoring run'}>
        <form onSubmit={runAll} className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3" dir="ltr">Lat</span>
            <input type="number" step="0.01" value={lat} onChange={(e) => setLat(e.target.value)} className={inputCls} /></label>
          <label className="flex flex-col gap-1"><span className="text-[11px] font-bold text-ink-3" dir="ltr">Lon</span>
            <input type="number" step="0.01" value={lon} onChange={(e) => setLon(e.target.value)} className={inputCls} /></label>
          <button type="submit" className="self-end rounded-xl bg-leaf-500 px-5 py-2.5 text-xs font-extrabold text-night-950">
            {isFa ? 'اجرای پایش' : 'Run monitoring'}
          </button>
        </form>
      </SectionCard>

      <SectionCard title={isFa ? 'گالری داده‌بنیان (جایگزین نمونهٔ مفهومی)' : 'Data-backed gallery (replaces the conceptual sample)'}>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {gallery.map((card) => (
            <div key={card.key} className="rounded-2xl bg-black/20 p-4">
              <div className="mb-2 flex items-center justify-between gap-2">
                <p className="text-[11px] font-bold text-ink-3">{card.title}</p>
                <Provenance source={card.source} />
              </div>
              <p className="text-lg font-extrabold text-leaf-300" dir="ltr">{card.value}</p>
              {card.hint ? <p className="mt-1 text-[10px] leading-5 text-ink-3">{card.hint}</p> : null}
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard title={isFa ? 'صحنهٔ ماهواره‌ای (NDVI/EVI/SAVI)' : 'Satellite scene (NDVI/EVI/SAVI)'}>
        <StateBanner state={scene.state} error={scene.error} kind={scene.kind} retry={() => undefined} />
        {sceneResult ? <KeyValues data={sceneResult} /> : null}
        {!sceneResult && scene.state !== 'loading' ? (
          <p className="mt-2 text-[11px] leading-6 text-ink-3">
            {isFa
              ? 'این نقطهٔ اتصال، برای حفظ صحت داده، فقط با اعتبارنامهٔ کوپرنیکوس (CDSE) صحنهٔ واقعی برمی‌گرداند؛ بدون آن، صفحه به‌جای عدد ساختگی، «در دسترس نیست» نشان می‌دهد.'
              : 'To preserve data honesty this endpoint returns real scenes only with Copernicus (CDSE) credentials; without them the page shows “unavailable” instead of a fabricated number.'}
          </p>
        ) : null}
      </SectionCard>

      <SectionCard title={isFa ? 'هواشناسی و سری ERA5' : 'Weather & ERA5 series'}>
        <StateBanner state={weather.state} error={weather.error} kind={weather.kind} retry={() => undefined} />
        {weatherResult ? <KeyValues data={weatherResult} /> : null}
      </SectionCard>

      <SectionCard title={isFa ? 'فرسایش خاک (سمت سرور)' : 'Soil erosion (server-side)'}>
        <StateBanner state={erosion.state} error={erosion.error} kind={erosion.kind} retry={() => undefined} />
        {erosionResult ? <KeyValues data={erosionResult} /> : null}
      </SectionCard>
    </div>
  );
}
