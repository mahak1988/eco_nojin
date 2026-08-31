import React from 'react';
import { AnimatedCounter } from '../ui/AnimatedCounter';
import type { RealLandResult, ScientificChainResult } from '../../types/vll';

interface LiveMetricStripProps {
  realLand: RealLandResult | null;
  chain: ScientificChainResult | null;
}

const num = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null);

/**
 * نوار متریک زنده — شمارنده‌های انیمیشنی (count-up) با مقادیر واقعی ERA5/SoilGrids/زنجیره علمی.
 * بدون داده واقعی، «—» نمایش داده می‌شود (هیچ fallback ساختگی).
 */
export const LiveMetricStrip: React.FC<LiveMetricStripProps> = ({ realLand, chain }) => {
  const climate = realLand?.climate;
  const soil = realLand?.soil;
  const erosion = chain?.erosion?.soil_loss_ton_ha_yr;
  const socFinal = num(chain?.rothc?.summary?.soc_final_t_ha);
  const yieldT = num(chain?.aquacrop?.summary?.yield_ton_ha);
  const reliability = num(chain?.water?.summary?.supply_reliability_pct);

  const metrics: {
    label: string;
    value: number | null;
    suffix: string;
    decimals: number;
    color: string;
    icon: string;
  }[] = [
    {
      label: 'بارش سالانه',
      value: climate?.annual_rainfall_mm ?? null,
      suffix: 'mm',
      decimals: 1,
      color: '#3b82f6',
      icon: '🌧️',
    },
    {
      label: 'دمای میانگین',
      value: climate?.avg_temp_c ?? null,
      suffix: '°C',
      decimals: 1,
      color: '#f59e0b',
      icon: '🌡️',
    },
    {
      label: 'ET0 سالانه',
      value: climate?.annual_et0_mm ?? null,
      suffix: 'mm',
      decimals: 0,
      color: '#ef4444',
      icon: '💨',
    },
    {
      label: 'کربن خاک (SOC)',
      value: socFinal ?? soil?.soc_pct ?? null,
      suffix: 't/ha',
      decimals: 1,
      color: '#10b981',
      icon: '🌱',
    },
    {
      label: 'فرسایش',
      value: erosion ?? null,
      suffix: 't/ha/yr',
      decimals: 2,
      color: '#a16207',
      icon: '⛰️',
    },
    {
      label: 'عملکرد گندم',
      value: yieldT ?? null,
      suffix: 't/ha',
      decimals: 2,
      color: '#eab308',
      icon: '🌾',
    },
    {
      label: 'قابلیت اطمینان آب',
      value: reliability ?? null,
      suffix: '٪',
      decimals: 1,
      color: '#06b6d4',
      icon: '💧',
    },
    {
      label: 'pH خاک',
      value: soil?.ph_h2o ?? null,
      suffix: '',
      decimals: 1,
      color: '#8b5cf6',
      icon: '🧪',
    },
  ];

  return (
    <div className="card" style={{ padding: '1rem', marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.9rem' }}>
        <span
          style={{
            width: 10,
            height: 10,
            borderRadius: '50%',
            background: realLand?.climate?.status === 'ok' ? '#22c55e' : '#f59e0b',
            animation: 'livePulse 1.6s ease-in-out infinite',
          }}
        />
        <span style={{ fontSize: '0.85rem', fontWeight: 700 }}>متریک‌های زنده — داده واقعی</span>
        <span style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>
          {realLand?.climate?.data_source ?? ''} · {realLand?.soil?.data_source ?? ''}
        </span>
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: '0.6rem',
        }}
      >
        {metrics.map((m) => (
          <div
            key={m.label}
            style={{
              padding: '0.6rem 0.8rem',
              borderRadius: 12,
              background: 'var(--color-bg)',
              border: '1px solid var(--color-border)',
            }}
          >
            <div
              style={{
                fontSize: '0.72rem',
                color: 'var(--color-text-secondary)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.3rem',
              }}
            >
              <span>{m.icon}</span> {m.label}
            </div>
            <div style={{ fontSize: '1.15rem', fontWeight: 800, color: m.color }}>
              {m.value != null ? (
                <AnimatedCounter
                  value={m.value}
                  decimals={m.decimals}
                  suffix={` ${m.suffix}`}
                  duration={1200}
                />
              ) : (
                '—'
              )}
            </div>
          </div>
        ))}
      </div>
      <style>{`@keyframes livePulse { 0%,100% { opacity: 1; box-shadow: 0 0 0 0 rgba(34,197,94,0.5);} 50% { opacity: 0.6; box-shadow: 0 0 0 6px rgba(34,197,94,0);} }`}</style>
    </div>
  );
};
