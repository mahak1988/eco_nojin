import React from 'react';
import { Grid3X3, KeyRound, Satellite } from 'lucide-react';
import type { RealSatelliteBlock } from '../../types/vll';

interface NdviGridCardProps {
  satellite?: RealSatelliteBlock;
}

const ndviColor = (v: number): string => {
  // سبز پررنگ (پوشش بالا) → قهوه‌ای (خاک لخت)
  const t = Math.max(0, Math.min(1, (v + 0.2) / 0.8));
  const r = Math.round(34 + (139 - 34) * (1 - t));
  const g = Math.round(139 + (34 - 139) * (1 - t)) + 40;
  const b = 34;
  return `rgb(${Math.min(255, r)}, ${Math.min(255, g)}, ${b})`;
};

/**
 * لایه NDVI گرید ۷×۷ از ماهواره واقعی (CDSE, Sentinel-2).
 * بدون اعتبارنامه، وضعیت صادقانه «نیاز به اعتبار» نمایش داده می‌شود — هیچ داده ساختگی.
 */
export const NdviGridCard: React.FC<NdviGridCardProps> = ({ satellite }) => {
  const grid = satellite?.ndvi_grid;
  const status = satellite?.status;

  if (!satellite || (status !== 'ok' && status !== 'partial')) {
    return (
      <div className="card" style={{ padding: '1rem 1.25rem' }}>
        <h4 style={{ fontSize: '0.95rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.45rem', margin: '0 0 0.5rem' }}>
          <Grid3X3 size={16} color="var(--color-primary)" /> لایه NDVI ماهواره
        </h4>
        <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <KeyRound size={14} /> نیاز به اعتبارنامه رایگان CDSE (Copernicus) — با افزودن به .env فعال می‌شود.
        </p>
      </div>
    );
  }

  if (!grid || grid.length === 0) {
    return (
      <div className="card" style={{ padding: '1rem 1.25rem' }}>
        <h4 style={{ fontSize: '0.95rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.45rem', margin: '0 0 0.5rem' }}>
          <Grid3X3 size={16} color="var(--color-primary)" /> لایه NDVI ماهواره
        </h4>
        <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--color-text-secondary)' }}>گرید NDVI برای این محدوده موجود نیست.</p>
      </div>
    );
  }

  const sorted = [...grid].sort((a, b) => b.lat - a.lat || a.lon - b.lon);
  const avg = grid.reduce((s, p) => s + p.ndvi, 0) / grid.length;

  return (
    <div className="card" style={{ padding: '1rem 1.25rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
        <h4 style={{ fontSize: '0.95rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.45rem', margin: 0 }}>
          <Grid3X3 size={16} color="var(--color-primary)" /> NDVI واقعی (Sentinel-2)
        </h4>
        <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
          <Satellite size={11} /> میانگین {avg.toFixed(2)}
        </span>
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${Math.ceil(Math.sqrt(sorted.length))}, 1fr)`,
          gap: 3,
          direction: 'ltr',
        }}
      >
        {sorted.map((p, i) => (
          <div
            key={i}
            title={`NDVI ${p.ndvi.toFixed(2)} @ ${p.lat.toFixed(4)}, ${p.lon.toFixed(4)}`}
            style={{ aspectRatio: '1', borderRadius: 3, background: ndviColor(p.ndvi) }}
          />
        ))}
      </div>
      <p style={{ margin: '0.5rem 0 0', fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>
        سنسور: {satellite.sensor ?? 'S2'} · {satellite.sensed_at ? `تصویر ${satellite.sensed_at.slice(0, 10)}` : ''} · {satellite.cloud_cover != null ? `ابر ${satellite.cloud_cover.toFixed(0)}٪` : ''}
      </p>
    </div>
  );
};
