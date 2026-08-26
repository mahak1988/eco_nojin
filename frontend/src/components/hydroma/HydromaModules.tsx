import React from 'react';
import ReactECharts from 'echarts-for-react';
import {
  CloudRain, Layers, Mountain, Leaf, Sprout, Waves, AlertTriangle, Cpu, Database, Box,
} from 'lucide-react';
import type { RealLandResult, ScientificChainResult } from '../../types/vll';
import type { SceneMode } from './DashboardScene3D';

const num = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null);

/* ---------- کوچک‌ها ---------- */
const Field: React.FC<{ label: string; value: React.ReactNode; strong?: boolean }> = ({ label, value, strong }) => (
  <div style={{ padding: '0.45rem 0.6rem', borderRadius: 8, background: 'var(--color-bg)', border: '1px solid var(--color-border)' }}>
    <div style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)' }}>{label}</div>
    <div style={{ fontSize: strong ? '0.95rem' : '0.85rem', fontWeight: strong ? 800 : 600 }}>{value}</div>
  </div>
);

const MONTHS = ['فرو', 'ارد', 'خرد', 'تیر', 'مرد', 'شهر', 'مهر', 'آبا', 'آذر', 'دی', 'بهم', 'اسف'];

const ModuleCard: React.FC<{
  title: string; icon: React.ReactNode; mode: SceneMode; color: string;
  onView3D: (m: SceneMode) => void; children: React.ReactNode;
}> = ({ title, icon, mode, color, onView3D, children }) => (
  <div className="card" style={{ padding: '1.1rem', display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <h3 style={{ fontSize: '1rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', color }}>
        {icon} {title}
      </h3>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, animation: 'livePulse 1.8s ease-in-out infinite' }} />
        <button
          onClick={() => onView3D(mode)}
          title="مشاهده سه‌بعدی این ماژول"
          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', padding: '0.3rem 0.7rem', borderRadius: 999, border: '1px solid var(--color-border)', background: 'var(--color-bg)', cursor: 'pointer', fontSize: '0.72rem', fontWeight: 700 }}
        >
          <Box size={13} /> سه‌بعدی
        </button>
      </div>
    </div>
    {children}
  </div>
);

const echartsTheme = {
  textStyle: { fontFamily: 'inherit' },
  grid: { top: 30, bottom: 24, left: 36, right: 12 },
};

interface HydromaModulesProps {
  realLand: RealLandResult | null;
  chain: ScientificChainResult | null;
  onView3D: (m: SceneMode) => void;
}

/**
 * ماژول‌های داشبورد — هر ماژول: فیلدهای متعدد (داده واقعی) + چارت (سری واقعی) + دکمه سه‌بعدی.
 * همه مقادیر از بک‌اند/موتورها می‌آیند؛ بدون داده، «—» نمایش داده می‌شود.
 */
export const HydromaModules: React.FC<HydromaModulesProps> = ({ realLand, chain, onView3D }) => {
  const climate = realLand?.climate;
  const soil = realLand?.soil;
  const sat = realLand?.satellite;
  const erosion = chain?.erosion;
  const rothc = chain?.rothc;
  const aquacrop = chain?.aquacrop;
  const water = chain?.water;
  const flood = chain?.flood;
  const opt = chain?.optimization;
  const swat = chain?.swat;
  const inputs = chain?.inputs ?? {};

  const monthlyPrecip = climate?.monthly?.precip_mm ?? [];
  const monthlyTmax = climate?.monthly?.tmax_c ?? [];
  const socSeries = (rothc?.outputs?.annual_series as number[] | undefined) ?? [];
  const pools = (rothc?.outputs?.pools as Record<string, number> | undefined) ?? null;
  const supplySeries = (water?.outputs?.supply_series as number[] | undefined) ?? [];
  const storageSeries = (water?.outputs?.storage_series as number[] | undefined) ?? [];
  const pareto = (opt?.outputs?.pareto_front as Array<{ erosion_t_ha_yr: number; yield_ton_ha: number; deficit_mcm: number }> | undefined) ?? [];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(430px, 1fr))', gap: '1.2rem' }}>
      {/* ── اقلیم ─────────────────────────────── */}
      <ModuleCard title="اقلیم (ERA5)" icon={<CloudRain size={17} />} mode="climate" color="#3b82f6" onView3D={onView3D}>
        <ReactECharts
          style={{ height: 200 }}
          option={{
            ...echartsTheme,
            tooltip: { trigger: 'axis' },
            legend: { data: ['بارش (mm)', 'دمای بیشینه (°C)'], top: 0, textStyle: { fontSize: 10 } },
            xAxis: { type: 'category', data: MONTHS, axisLabel: { fontSize: 9 } },
            yAxis: [
              { type: 'value', name: 'mm', axisLabel: { fontSize: 9 } },
              { type: 'value', name: '°C', axisLabel: { fontSize: 9 } },
            ],
            series: [
              { name: 'بارش (mm)', type: 'bar', data: monthlyPrecip, itemStyle: { color: '#3b82f6', borderRadius: [3, 3, 0, 0] }, barMaxWidth: 16 },
              { name: 'دمای بیشینه (°C)', type: 'line', yAxisIndex: 1, data: monthlyTmax, smooth: true, itemStyle: { color: '#f59e0b' } },
            ],
          }}
        />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '0.4rem' }}>
          <Field label="بارش سالانه" value={`${num(climate?.annual_rainfall_mm)?.toFixed(1) ?? '—'} mm`} strong />
          <Field label="دمای میانگین" value={`${num(climate?.avg_temp_c)?.toFixed(1) ?? '—'} °C`} strong />
          <Field label="ET0 سالانه" value={`${num(climate?.annual_et0_mm)?.toFixed(0) ?? '—'} mm`} />
          <Field label="دمای بیشینه" value={`${num(climate?.max_temp_c)?.toFixed(1) ?? '—'} °C`} />
          <Field label="دمای کمینه" value={`${num(climate?.min_temp_c)?.toFixed(1) ?? '—'} °C`} />
          <Field label="آخرین روز" value={climate?.latest?.date ? String(climate.latest.date).slice(5) : '—'} />
        </div>
      </ModuleCard>

      {/* ── خاک ───────────────────────────────── */}
      <ModuleCard title="خاک (SoilGrids)" icon={<Layers size={17} />} mode="soil" color="#a16207" onView3D={onView3D}>
        <ReactECharts
          style={{ height: 200 }}
          option={{
            ...echartsTheme,
            tooltip: {},
            radar: {
              indicator: [
                { name: 'شن', max: 100 }, { name: 'سیلت', max: 100 }, { name: 'رس', max: 100 },
                { name: 'SOC (g/kg)', max: 30 }, { name: 'CEC', max: 40 }, { name: 'pH', max: 14 },
              ],
              radius: '62%',
            },
            series: [{
              type: 'radar',
              data: [{
                value: [num(soil?.sand_pct) ?? 0, num(soil?.silt_pct) ?? 0, num(soil?.clay_pct) ?? 0, num(soil?.soc_g_kg) ?? 0, num(soil?.cec_mmolc_kg) ?? 0, num(soil?.ph_h2o) ?? 0],
                name: 'خاک',
                areaStyle: { color: 'rgba(161,98,7,0.3)' },
                itemStyle: { color: '#a16207' },
              }],
            }],
          }}
        />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '0.4rem' }}>
          <Field label="بافت" value={String(soil?.texture ?? '—')} strong />
          <Field label="شن/سیلت/رس" value={`${num(soil?.sand_pct)?.toFixed(0) ?? '—'}/${num(soil?.silt_pct)?.toFixed(0) ?? '—'}/${num(soil?.clay_pct)?.toFixed(0) ?? '—'}٪`} />
          <Field label="SOC" value={soil?.soc_pct != null ? `${soil.soc_pct.toFixed(2)}٪` : '—'} strong />
          <Field label="pH" value={num(soil?.ph_h2o)?.toFixed(1) ?? '—'} />
          <Field label="CEC" value={`${num(soil?.cec_mmolc_kg)?.toFixed(1) ?? '—'} cmol/kg`} />
          <Field label="جرم مخصوص" value={`${num(soil?.bulk_density_g_cm3)?.toFixed(2) ?? '—'} g/cm³`} />
          <Field label="K (RUSLE)" value={num(soil?.k_factor_rusle)?.toFixed(4) ?? '—'} />
          <Field label="منبع" value={String(soil?.data_source ?? '—')} />
        </div>
      </ModuleCard>

      {/* ── فرسایش ────────────────────────────── */}
      <ModuleCard title="فرسایش (RUSLE)" icon={<Mountain size={17} />} mode="erosion" color="#ef4444" onView3D={onView3D}>
        <ReactECharts
          style={{ height: 200 }}
          option={{
            ...echartsTheme,
            tooltip: { trigger: 'axis' },
            xAxis: { type: 'category', data: ['R', 'K', 'LS', 'C', 'P'], axisLabel: { fontSize: 11, fontWeight: 700 } },
            yAxis: { type: 'value', axisLabel: { fontSize: 9 } },
            series: [{
              type: 'bar',
              data: [
                { value: num(erosion?.r_factor) ?? 0, itemStyle: { color: '#3b82f6' } },
                { value: (num(erosion?.k_factor) ?? 0) * 100, itemStyle: { color: '#f59e0b' } },
                { value: num(erosion?.ls_factor) ?? 0, itemStyle: { color: '#ef4444' } },
                { value: (num(erosion?.c_factor) ?? 0) * 100, itemStyle: { color: '#10b981' } },
                { value: num(erosion?.p_factor) ?? 0, itemStyle: { color: '#8b5cf6' } },
              ],
              barMaxWidth: 30,
            }],
          }}
        />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '0.4rem' }}>
          <Field label="هدررفت خاک" value={`${num(erosion?.soil_loss_ton_ha_yr)?.toFixed(2) ?? '—'} t/ha/yr`} strong />
          <Field label="ریسک" value={String(erosion?.risk ?? '—')} strong />
          <Field label="R (باران)" value={num(erosion?.r_factor)?.toFixed(1) ?? '—'} />
          <Field label="K (خاک)" value={num(erosion?.k_factor)?.toFixed(4) ?? '—'} />
          <Field label="LS (شیب)" value={num(erosion?.ls_factor)?.toFixed(2) ?? '—'} />
          <Field label="C (پوشش)" value={num(erosion?.c_factor)?.toFixed(2) ?? '—'} />
          <Field label="P (مدیریت)" value={num(erosion?.p_factor)?.toFixed(2) ?? '—'} />
        </div>
      </ModuleCard>

      {/* ── کربن ──────────────────────────────── */}
      <ModuleCard title="کربن خاک (RothC)" icon={<Leaf size={17} />} mode="carbon" color="#10b981" onView3D={onView3D}>
        <ReactECharts
          style={{ height: 200 }}
          option={{
            ...echartsTheme,
            tooltip: { trigger: 'axis' },
            xAxis: { type: 'category', data: socSeries.map((_, i) => `سال ${i + 1}`), axisLabel: { fontSize: 9, interval: Math.max(0, Math.floor(socSeries.length / 8)) } },
            yAxis: { type: 'value', name: 't C/ha', axisLabel: { fontSize: 9 } },
            series: [{
              name: 'SOC', type: 'line', data: socSeries, smooth: true,
              areaStyle: { opacity: 0.18 }, itemStyle: { color: '#10b981' }, lineStyle: { width: 2.5 },
            }],
          }}
        />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '0.4rem' }}>
          <Field label="SOC اولیه" value={`${num(rothc?.outputs?.initial_soc_t_ha)?.toFixed(1) ?? '—'} t/ha`} />
          <Field label="SOC نهایی" value={`${num(rothc?.summary?.soc_final_t_ha)?.toFixed(1) ?? '—'} t/ha`} strong />
          <Field label="تغییر سالانه" value={`${num(rothc?.summary?.soc_change_t_ha_yr)?.toFixed(3) ?? '—'} t/ha/yr`} />
          <Field label="سال‌ها" value={String(rothc?.outputs?.years ?? '—')} />
          <Field label="موتور" value={String(rothc?.outputs?.engine ?? '—')} />
          {pools && Object.entries(pools).map(([k, v]) => (
            <Field key={k} label={`استخر ${k}`} value={`${v.toFixed(2)} t/ha`} />
          ))}
        </div>
      </ModuleCard>

      {/* ── محصول ─────────────────────────────── */}
      <ModuleCard title="محصول (AquaCrop)" icon={<Sprout size={17} />} mode="crop" color="#eab308" onView3D={onView3D}>
        <ReactECharts
          style={{ height: 200 }}
          option={{
            ...echartsTheme,
            tooltip: { trigger: 'axis' },
            xAxis: { type: 'category', data: ['عملکرد', 'زی‌توده'], axisLabel: { fontSize: 11, fontWeight: 700 } },
            yAxis: { type: 'value', name: 't/ha', axisLabel: { fontSize: 9 } },
            series: [{
              type: 'bar',
              data: [
                { value: num(aquacrop?.summary?.yield_ton_ha) ?? 0, itemStyle: { color: '#eab308' } },
                { value: num(aquacrop?.outputs?.biomass_ton_ha) ?? 0, itemStyle: { color: '#84cc16' } },
              ],
              barMaxWidth: 40,
            }],
          }}
        />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '0.4rem' }}>
          <Field label="عملکرد" value={`${num(aquacrop?.summary?.yield_ton_ha)?.toFixed(2) ?? '—'} t/ha`} strong />
          <Field label="زی‌توده" value={`${num(aquacrop?.outputs?.biomass_ton_ha)?.toFixed(2) ?? '—'} t/ha`} />
          <Field label="آبیاری" value={`${num(aquacrop?.summary?.irrigation_mm)?.toFixed(0) ?? '—'} mm`} />
          <Field label="بهره‌وری آب" value={`${num(aquacrop?.outputs?.water_productivity_kg_m3)?.toFixed(2) ?? '—'} kg/m³`} />
          <Field label="برداشت" value={String(aquacrop?.outputs?.harvest_date ?? '—')} />
          <Field label="محصول" value={String(aquacrop?.outputs?.crop ?? '—')} />
        </div>
      </ModuleCard>

      {/* ── آب ────────────────────────────────── */}
      <ModuleCard title="تخصیص آب (Pywr)" icon={<Waves size={17} />} mode="water" color="#06b6d4" onView3D={onView3D}>
        <ReactECharts
          style={{ height: 200 }}
          option={{
            ...echartsTheme,
            tooltip: { trigger: 'axis' },
            legend: { data: ['تأمین', 'ذخیره'], top: 0, textStyle: { fontSize: 10 } },
            xAxis: { type: 'category', data: supplySeries.map((_, i) => `ماه ${i + 1}`), axisLabel: { fontSize: 9, interval: 1 } },
            yAxis: { type: 'value', name: 'MCM', axisLabel: { fontSize: 9 } },
            series: [
              { name: 'تأمین', type: 'bar', data: supplySeries, itemStyle: { color: '#3b82f6', borderRadius: [3, 3, 0, 0] }, barMaxWidth: 12 },
              { name: 'ذخیره', type: 'line', data: storageSeries, smooth: true, itemStyle: { color: '#06b6d4' } },
            ],
          }}
        />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '0.4rem' }}>
          <Field label="قابلیت اطمینان" value={`${num(water?.summary?.supply_reliability_pct)?.toFixed(1) ?? '—'}٪`} strong />
          <Field label="کسری کل" value={`${num(water?.summary?.total_deficit_mcm)?.toFixed(2) ?? '—'} MCM`} />
          <Field label="تقاضای کل" value={`${num(water?.outputs?.total_demand_mcm)?.toFixed(2) ?? '—'} MCM`} />
          <Field label="تأمین کل" value={`${num(water?.outputs?.total_supply_mcm)?.toFixed(2) ?? '—'} MCM`} />
          <Field label="شبکه" value={String(water?.outputs?.network ?? '—')} />
          <Field label="رواناب ورودی" value={`${num(inputs?.annual_runoff_mcm)?.toFixed(3) ?? '—'} MCM`} />
        </div>
      </ModuleCard>

      {/* ── سیلاب ─────────────────────────────── */}
      <ModuleCard title="سیلاب (HEC-RAS)" icon={<AlertTriangle size={17} />} mode="flood" color="#8b5cf6" onView3D={onView3D}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
          <Field label="ارتفاع آب (Manning)" value={`${num(flood?.summary?.wse_m)?.toFixed(2) ?? '—'} m`} strong />
          <Field label="موتور" value={String(flood?.summary?.engine ?? '—')} />
          <Field label="وضعیت" value={String(flood?.status ?? '—')} />
        </div>
        <p style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', margin: 0 }}>
          {flood?.summary?.requires_hecras_install === true
            ? <>باینری رایگان HEC-RAS نصب نیست — با نصب آن، عمق و پهنه سیلاب واقعی (و رندر deck.gl) فعال می‌شود: <a href="https://www.hec.usace.army.mil/software/hec-ras/download.aspx" target="_blank" rel="noreferrer">دانلود از USACE</a></>
            : 'خروجی HEC-RAS پس از اجرای واقعی نمایش داده می‌شود.'}
        </p>
      </ModuleCard>

      {/* ── بهینه‌سازی ────────────────────────── */}
      <ModuleCard title="بهینه‌سازی (NSGA-II)" icon={<Cpu size={17} />} mode="optimize" color="#ec4899" onView3D={onView3D}>
        <ReactECharts
          style={{ height: 200 }}
          option={{
            ...echartsTheme,
            tooltip: { trigger: 'item', formatter: (p: { data: [number, number, number] }) => `فرسایش ${p.data[0].toFixed(2)} · عملکرد ${p.data[1].toFixed(2)} · کسری ${p.data[2].toFixed(2)}` },
            xAxis: { type: 'value', name: 'فرسایش t/ha/yr', axisLabel: { fontSize: 9 }, scale: true },
            yAxis: { type: 'value', name: 'عملکرد t/ha', axisLabel: { fontSize: 9 }, scale: true },
            series: [{
              type: 'scatter',
              symbolSize: 14,
              data: pareto.map((p) => [p.erosion_t_ha_yr, p.yield_ton_ha, p.deficit_mcm] as [number, number, number]),
              itemStyle: { color: '#ec4899' },
            }],
          }}
        />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '0.4rem' }}>
          <Field label="راه‌حل‌های پارتو" value={String(opt?.outputs?.pareto_size ?? opt?.summary?.pareto_size ?? '—')} strong />
          <Field label="بهترین عملکرد" value={`${num(opt?.summary?.best_yield_t_ha)?.toFixed(2) ?? '—'} t/ha`} />
          <Field label="کمترین فرسایش" value={`${num(opt?.summary?.min_erosion_t_ha_yr)?.toFixed(2) ?? '—'} t/ha/yr`} />
          <Field label="نسل‌ها" value={String(opt?.outputs?.n_generations ?? '—')} />
          <Field label="جمعیت" value={String(opt?.outputs?.pop_size ?? '—')} />
          <Field label="حالت" value={String(opt?.summary?.mode ?? '—')} />
        </div>
      </ModuleCard>

      {/* ── SWAT+ ─────────────────────────────── */}
      <ModuleCard title="SWAT+ (آماده‌سازی)" icon={<Database size={17} />} mode="idle" color="#64748b" onView3D={onView3D}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '0.4rem' }}>
          <Field label="وضعیت" value={String(swat?.status ?? '—')} strong />
          <Field label="شیب" value={`${num(inputs?.slope_pct)?.toFixed(1) ?? '—'}٪`} />
          <Field label="بارش" value={`${num(inputs?.annual_rainfall_mm)?.toFixed(1) ?? '—'} mm`} />
          <Field label="رواناب" value={`${num(inputs?.annual_runoff_mcm)?.toFixed(3) ?? '—'} MCM`} />
          <Field label="رس خاک" value={`${num(inputs?.clay_pct)?.toFixed(1) ?? '—'}٪`} />
          <Field label="SOC اولیه" value={`${num(inputs?.soc_initial_t_ha)?.toFixed(1) ?? '—'} t/ha`} />
          <Field label="بافت" value={String(inputs?.soil_texture ?? '—')} />
          <Field label="مدیریت" value={String(inputs?.practice ?? '—')} />
        </div>
        <p style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', margin: 0 }}>
          {swat?.summary?.run_requires_executable === true && (
            <>اجرای کامل نیازمند باینری رایگان: <a href="https://swat.tamu.edu/software/plus/" target="_blank" rel="noreferrer">دانلود SWAT+ از Texas A&amp;M</a></>
          )}
        </p>
      </ModuleCard>

      {/* ── ماهواره ───────────────────────────── */}
      <ModuleCard title="ماهواره (CDSE)" icon={<Layers size={17} />} mode="idle" color="#22c55e" onView3D={onView3D}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '0.4rem' }}>
          <Field label="وضعیت" value={String(sat?.status ?? '—')} strong />
          <Field label="NDVI" value={sat?.ndvi != null ? sat.ndvi.toFixed(3) : '—'} />
          <Field label="EVI" value={sat?.evi != null ? sat.evi.toFixed(3) : '—'} />
          <Field label="LAI" value={sat?.lai != null ? sat.lai.toFixed(2) : '—'} />
          <Field label="LST" value={sat?.lst_c != null ? `${sat.lst_c.toFixed(1)} °C` : '—'} />
          <Field label="سنسور" value={String(sat?.sensor ?? '—')} />
          <Field label="تصویر" value={sat?.sensed_at ? String(sat.sensed_at).slice(0, 10) : '—'} />
          <Field label="ابر" value={sat?.cloud_cover != null ? `${sat.cloud_cover.toFixed(0)}٪` : '—'} />
        </div>
        <p style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', margin: 0 }}>
          {sat?.status === 'credentials_required' && (
            <>اعتبارنامه رایگان CDSE لازم است — با افزودن به .env، NDVI/LAI/C-factor واقعی Sentinel-2 فعال می‌شود.</>
          )}
        </p>
      </ModuleCard>
    </div>
  );
};
