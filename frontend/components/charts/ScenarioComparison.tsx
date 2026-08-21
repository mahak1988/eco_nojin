"use client";
import { useEffect, useMemo, useRef, useState } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ComposedChart, Bar, Line,
} from 'recharts';
import { motion } from 'framer-motion';
import { TrendingUp, AlertTriangle, Download, RefreshCw, Sparkles } from 'lucide-react';
import html2canvas from 'html2canvas';

import { useTheme } from '../../lib/theme-context';
import { useFarm } from '../../lib/farm-context';
import { useI18n } from '../../lib/i18n-context';
import { api } from '../../lib/api-client';
import { MotionIcon } from '@/components/ui/motion-icon';
import { Skeleton } from '@/components/ui/skeleton';

const SSP_COLORS: Record<string, string> = {
  ssp126: '#10b981',
  ssp245: '#f59e0b',
  ssp370: '#ef4444',
  ssp585: '#7c2d12',
};

const SSP_LABELS: Record<string, string> = {
  ssp126: 'SSP1-2.6 (Best)',
  ssp245: 'SSP2-4.5 (Moderate)',
  ssp370: 'SSP3-7.0 (Bad)',
  ssp585: 'SSP5-8.5 (Worst)',
};

const YEARS = [2030, 2040, 2050, 2060, 2070, 2080, 2090, 2100];
const SSP_KEYS = ['ssp126', 'ssp245', 'ssp370', 'ssp585'];

const SSP_ANOMALY: Record<string, { temp: number; precip: number }> = {
  ssp126: { temp: 1.2, precip: -3 },
  ssp245: { temp: 2.2, precip: -8 },
  ssp370: { temp: 3.2, precip: -13 },
  ssp585: { temp: 4.0, precip: -18 },
};

interface ScenarioRow {
  scenario: string;
  label: string;
  tempChange: number;
  precipChange: number;
  droughtRisk: number;
  projectedTemp: number;
  projectedPrecip: number;
}

// ------------------ کامپوننت تورتیپ سفارشی (انیمیشن‌دار) ------------------
const CustomTooltip = ({ active, payload, label, unit = '°C' }: any) => {
  if (active && payload && payload.length) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(8px)',
          padding: '12px 16px',
          borderRadius: '12px',
          border: '1px solid #e5e7eb',
          boxShadow: '0 10px 30px rgba(0,0,0,0.1)',
          direction: 'ltr',
          fontFamily: 'Vazirmatn, Tahoma, sans-serif',
        }}
      >
        <p style={{ fontWeight: 'bold', marginBottom: '6px', fontSize: '0.9rem', color: '#1f2937' }}>
          {label}
        </p>
        {payload.map((entry: any, index: number) => (
          <p key={index} style={{ color: entry.color, fontSize: '0.85rem', margin: '2px 0' }}>
            {entry.name}: {entry.value.toFixed(1)}{unit}
          </p>
        ))}
      </motion.div>
    );
  }
  return null;
};

export default function ScenarioComparison({ baselineTemp = 18.5, baselinePrecip = 380 }) {
  const { colors } = useTheme();
  const { selectedFarm } = useFarm();
  const { t } = useI18n();
  const [data, setData] = useState<ScenarioRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [year, setYear] = useState(2100);
  const [active, setActive] = useState<Set<string>>(new Set(SSP_KEYS));
  const [exporting, setExporting] = useState(false);
  const boardRef = useRef<HTMLDivElement>(null);

  const runAllScenarios = async () => {
    setLoading(true);
    setError(null);
    const results: ScenarioRow[] = [];
    try {
      for (const sc of SSP_KEYS) {
        const res = await api.post<any>('/api/v1/scenarios/apply', {
          baseline_temp: baselineTemp,
          baseline_precip: baselinePrecip,
          scenario: sc,
          year: 2050,
          farm_id: selectedFarm?.id,
        });
        if (res.success && res.data) {
          results.push({
            scenario: sc,
            label: SSP_LABELS[sc],
            tempChange: res.data.temperature_change,
            precipChange: res.data.precipitation_change_percent,
            droughtRisk: res.data.drought_risk_index,
            projectedTemp: res.data.projected_temperature,
            projectedPrecip: res.data.projected_precipitation,
          });
        }
      }
      if (results.length === 0) throw new Error('empty');
      setData(results);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runAllScenarios();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedFarm]);

  const timelineData = useMemo(
    () =>
      YEARS.filter((y) => y <= year).map((yr) => {
        const row: Record<string, number> = { year: yr };
        SSP_KEYS.forEach((sc) => {
          const a = SSP_ANOMALY[sc];
          const scale = Math.min((yr - 2020) / 30, 1.5);
          row[`${sc}_temp`] = +(baselineTemp + a.temp * scale).toFixed(2);
          row[`${sc}_precip`] = +(baselinePrecip * (1 + (a.precip / 100) * scale)).toFixed(1);
        });
        return row;
      }),
    [baselineTemp, baselinePrecip, year]
  );

  const visibleCards = data.filter((d) => active.has(d.scenario));

  const insights = useMemo(() => {
    if (data.length === 0) return [];
    const worst = [...data].sort((a, b) => b.tempChange - a.tempChange)[0];
    const out: string[] = [];
    out.push(
      t('scenario_insights_warming')
        .replace('{scenario}', worst.label)
        .replace('{delta}', '+' + worst.tempChange.toFixed(1))
    );
    const precip = [...data].sort((a, b) => b.precipChange - a.precipChange)[0];
    out.push(
      t('scenario_insights_precip')
        .replace('{scenario}', precip.label)
        .replace('{pct}', precip.precipChange.toFixed(0))
    );
    const drought = [...data].sort((a, b) => b.droughtRisk - a.droughtRisk)[0];
    out.push(
      t('scenario_insights_drought').replace('{pct}', (drought.droughtRisk * 100).toFixed(0))
    );
    return out;
  }, [data, t]);

  const toggleScenario = (sc: string) => {
    setActive((prev) => {
      const next = new Set(prev);
      if (next.has(sc)) next.delete(sc);
      else next.add(sc);
      return next;
    });
  };

  const exportPng = async () => {
    if (!boardRef.current) return;
    setExporting(true);
    try {
      const canvas = await html2canvas(boardRef.current, { backgroundColor: colors.bg, scale: 2 });
      const link = document.createElement('a');
      link.download = 'eco-nojin-scenarios.png';
      link.href = canvas.toDataURL('image/png');
      link.click();
    } catch {
      /* export failed silently */
    } finally {
      setExporting(false);
    }
  };

  // skeleton
  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
          {[0, 1, 2, 3].map((i) => (
            <div key={i} style={{ padding: '16px', borderRadius: '14px', background: colors.cardBg, border: `1px solid ${colors.border}` }}>
              <Skeleton className="h-3 w-24 mb-3" />
              <Skeleton className="h-8 w-20 mb-3" />
              <Skeleton className="h-3 w-full" />
            </div>
          ))}
        </div>
        <Skeleton className="h-72 w-full" />
        <Skeleton className="h-56 w-full" />
      </div>
    );
  }

  // error
  if (error) {
    return (
      <div style={{
        padding: '32px', textAlign: 'center', color: colors.textMuted,
        background: colors.cardBg, borderRadius: '20px', border: `1px solid ${colors.border}`,
      }}>
        <AlertTriangle size={28} color={colors.warm} style={{ margin: '0 auto 12px' }} />
        <p style={{ margin: '0 0 16px' }}>{t('scenario_error')}</p>
        <button
          onClick={runAllScenarios}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: '6px',
            padding: '8px 16px', borderRadius: '10px', border: 'none', cursor: 'pointer',
            background: colors.primary, color: '#fff', fontSize: '0.85rem',
          }}
        >
          <RefreshCw size={14} /> {t('scenario_retry')}
        </button>
      </div>
    );
  }

  return (
    <div ref={boardRef} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Insights */}
      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        style={{
          background: colors.cardBg, padding: '16px 20px', borderRadius: '20px',
          border: `1px solid ${colors.border}`,
        }}
      >
        <h4 style={{ color: colors.text, margin: '0 0 8px', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={16} color={colors.primary} /> {t('scenario_insights_title')}
        </h4>
        <ul style={{ margin: 0, paddingRight: '18px', color: colors.textMuted, fontSize: '0.85rem', lineHeight: 1.9 }}>
          {insights.map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ul>
      </motion.div>

      {/* Controls */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {SSP_KEYS.map((sc) => {
            const on = active.has(sc);
            return (
              <button
                key={sc}
                onClick={() => toggleScenario(sc)}
                style={{
                  padding: '6px 12px', borderRadius: '999px', cursor: 'pointer', fontSize: '0.78rem',
                  border: `2px solid ${SSP_COLORS[sc]}${on ? 'cc' : '33'}`,
                  background: on ? `${SSP_COLORS[sc]}22` : 'transparent',
                  color: on ? SSP_COLORS[sc] : colors.textMuted,
                }}
                aria-pressed={on}
              >
                {SSP_LABELS[sc]}
              </button>
            );
          })}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <label style={{ fontSize: '0.8rem', color: colors.textMuted }}>
            {t('scenario_year')}: <strong style={{ color: colors.text }}>{year}</strong>
          </label>
          <input
            type="range" min={2030} max={2100} step={10} value={year}
            onChange={(e) => setYear(parseInt(e.target.value, 10))}
            style={{ width: '140px' }}
            aria-label={t('scenario_year')}
          />
          <button
            onClick={exportPng}
            disabled={exporting}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: '6px',
              padding: '8px 14px', borderRadius: '10px', border: `1px solid ${colors.border}`,
              cursor: 'pointer', background: colors.cardBg, color: colors.text, fontSize: '0.8rem',
            }}
          >
            <Download size={14} /> {exporting ? '...' : t('scenario_export')}
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
        {visibleCards.map((d, i) => (
          <motion.div
            key={d.scenario}
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            whileHover={{ y: -4 }}
            style={{
              padding: '16px', borderRadius: '14px',
              background: `${SSP_COLORS[d.scenario]}15`,
              border: `2px solid ${SSP_COLORS[d.scenario]}40`,
            }}
          >
            <div style={{ fontSize: '0.75rem', color: colors.textMuted, marginBottom: '4px' }}>
              {d.label}
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginBottom: '8px' }}>
              <MotionIcon name="thermometer" size={16} color={SSP_COLORS[d.scenario]} />
              <span style={{ fontSize: '1.5rem', fontWeight: '800', color: SSP_COLORS[d.scenario] }}>
                +{d.tempChange.toFixed(1)}°C
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: colors.textMuted }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                <MotionIcon name="rain" size={14} color={colors.accent} /> {d.precipChange.toFixed(1)}%
              </span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                <MotionIcon name="flame" size={14} color={colors.warm} /> {(d.droughtRisk * 100).toFixed(0)}%
              </span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* ⭐ Temperature Timeline — با AreaChart و گرادیانت سه‌بعدی ⭐ */}
      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        style={{
          background: colors.cardBg, padding: '20px', borderRadius: '20px',
          border: `1px solid ${colors.border}`,
        }}
      >
        <h4 style={{ color: colors.text, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <MotionIcon name="thermometer" size={18} color={colors.primary} /> {t('scenario_temp_projection')}
        </h4>
        <div dir="ltr">
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={timelineData}>
              <defs>
                {/* ایجاد گرادیانت برای هر سناریو */}
                {SSP_KEYS.filter((sc) => active.has(sc)).map((sc) => (
                  <linearGradient key={sc} id={`grad_${sc}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={SSP_COLORS[sc]} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={SSP_COLORS[sc]} stopOpacity={0.05} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
              <XAxis 
                dataKey="year" 
                stroke={colors.textMuted} 
                fontFamily="Vazirmatn, Tahoma, sans-serif"
                fontSize={11}
              />
              <YAxis
                stroke={colors.textMuted}
                unit="°C"
                domain={['dataMin - 1', 'dataMax + 1']}
                tickFormatter={(v: number) => v.toFixed(1)}
                fontFamily="Vazirmatn, Tahoma, sans-serif"
                fontSize={11}
              />
              <Tooltip content={<CustomTooltip unit="°C" />} />
              <Legend wrapperStyle={{ fontFamily: 'Vazirmatn, Tahoma, sans-serif', fontSize: 11 }} />
              {SSP_KEYS.filter((sc) => active.has(sc)).map((sc) => (
                <Area
                  key={sc}
                  type="monotone"
                  dataKey={`${sc}_temp`}
                  name={SSP_LABELS[sc]}
                  stroke={SSP_COLORS[sc]}
                  strokeWidth={2.5}
                  fill={`url(#grad_${sc})`}
                  fillOpacity={1}
                  dot={{ r: 3, fill: SSP_COLORS[sc], strokeWidth: 1, stroke: 'white' }}
                  activeDot={{ r: 8, stroke: 'white', strokeWidth: 2 }}
                  animationDuration={1500}
                  animationEasing="ease-in-out"
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* Precipitation Comparison */}
      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        style={{
          background: colors.cardBg, padding: '20px', borderRadius: '20px',
          border: `1px solid ${colors.border}`,
        }}
      >
        <h4 style={{ color: colors.text, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <MotionIcon name="rain" size={18} color={colors.accent} /> {t('scenario_compare_2050')}
        </h4>
        <div dir="ltr">
          <ResponsiveContainer width="100%" height={280}>
            <ComposedChart data={visibleCards}>
              <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
              <XAxis 
                dataKey="label" 
                stroke={colors.textMuted} 
                fontSize={11} 
                fontFamily="Vazirmatn, Tahoma, sans-serif"
              />
              <YAxis 
                yAxisId="left" 
                stroke={colors.textMuted} 
                unit="°C" 
                domain={['dataMin - 1', 'dataMax + 1']} 
                fontFamily="Vazirmatn, Tahoma, sans-serif"
                fontSize={11}
              />
              <YAxis 
                yAxisId="right" 
                orientation="right" 
                stroke={colors.textMuted} 
                unit="mm" 
                fontFamily="Vazirmatn, Tahoma, sans-serif"
                fontSize={11}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontFamily: 'Vazirmatn, Tahoma, sans-serif', fontSize: 11 }} />
              <Bar 
                yAxisId="left" 
                dataKey="projectedTemp" 
                fill={colors.primary} 
                name={`${t('scenario_temp_change')} (°C)`} 
                radius={[8, 8, 0, 0]} 
                animationDuration={1500} 
              />
              <Line 
                yAxisId="right" 
                type="monotone" 
                dataKey="projectedPrecip" 
                stroke={colors.accent} 
                strokeWidth={3} 
                name={`${t('scenario_precip_change')} (mm)`} 
                dot={{ r: 6, fill: colors.accent, stroke: 'white', strokeWidth: 2 }} 
                activeDot={{ r: 10 }}
                animationDuration={1500}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* Drought Risk Gauge */}
      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        style={{
          background: colors.cardBg, padding: '20px', borderRadius: '20px',
          border: `1px solid ${colors.border}`,
        }}
      >
        <h4 style={{ color: colors.text, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertTriangle size={18} color={colors.warm} /> {t('scenario_drought_risk')}
        </h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {visibleCards.map((d) => (
            <div key={d.scenario}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '0.85rem' }}>
                <span style={{ color: colors.text, fontWeight: '600' }}>{d.label}</span>
                <span style={{ color: SSP_COLORS[d.scenario], fontWeight: '700' }}>
                  {(d.droughtRisk * 100).toFixed(0)}%
                </span>
              </div>
              <div style={{ height: '10px', background: colors.bg, borderRadius: '5px', overflow: 'hidden' }}>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${d.droughtRisk * 100}%` }}
                  transition={{ duration: 1 }}
                  style={{
                    height: '100%',
                    background: `linear-gradient(90deg, ${colors.success}, ${colors.warm}, ${colors.danger})`,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}