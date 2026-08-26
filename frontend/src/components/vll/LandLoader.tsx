import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { MapPin, Upload, Globe, Mountain, Thermometer, Droplets } from 'lucide-react';
import { Card, Button } from '../ui';
import type { LandProfile, LandBBox } from '../../types/vll';

interface LandLoaderProps {
  onLandLoaded: (land: LandProfile) => void;
}

/**
 * نمونه زمین‌های از پیش تعریف‌شده (برای دمو)
 */
const SAMPLE_LANDS: LandProfile[] = [
  {
    id: 'demo-1',
    name: 'زمین بایر - حاشیه کویر مرکزی ایران',
    bbox: { north: 34.2, south: 34.1, east: 52.8, west: 52.7 },
    areaHa: 50,
    soil: {
      texture: 'sandy_loam',
      organicCarbonPct: 0.4,
      ph: 8.2,
      depthCm: 60,
      bulkDensity: 1.5,
      infiltrationRateMmHr: 25,
    },
    climate: {
      annualRainfallMm: 150,
      avgTempC: 22,
      maxTempC: 45,
      minTempC: -5,
      windSpeedMs: 8,
      windDirectionDeg: 320,
      solarRadiationMjM2: 22,
      evapotranspirationMm: 1800,
    },
    topography: {
      slopePct: 8,
      aspectDeg: 180,
      elevationM: 1100,
      curvature: 'convex',
    },
    currentLandUse: 'bare',
    ndvi: 0.15,
  },
  {
    id: 'demo-2',
    name: 'مزرعه دیم - کوهستان زاگرس',
    bbox: { north: 34.8, south: 34.7, east: 48.5, west: 48.4 },
    areaHa: 30,
    soil: {
      texture: 'loam',
      organicCarbonPct: 1.2,
      ph: 7.5,
      depthCm: 80,
      bulkDensity: 1.3,
      infiltrationRateMmHr: 18,
    },
    climate: {
      annualRainfallMm: 380,
      avgTempC: 14,
      maxTempC: 35,
      minTempC: -15,
      windSpeedMs: 5,
      windDirectionDeg: 270,
      solarRadiationMjM2: 18,
      evapotranspirationMm: 900,
    },
    topography: {
      slopePct: 15,
      aspectDeg: 200,
      elevationM: 1800,
      curvature: 'concave',
    },
    currentLandUse: 'cropland',
    ndvi: 0.45,
  },
  {
    id: 'demo-3',
    name: 'باغ پسته - کرمان',
    bbox: { north: 30.3, south: 30.2, east: 57.1, west: 57.0 },
    areaHa: 20,
    soil: {
      texture: 'clay_loam',
      organicCarbonPct: 0.8,
      ph: 7.8,
      depthCm: 120,
      bulkDensity: 1.4,
      infiltrationRateMmHr: 15,
    },
    climate: {
      annualRainfallMm: 140,
      avgTempC: 20,
      maxTempC: 42,
      minTempC: -10,
      windSpeedMs: 6,
      windDirectionDeg: 310,
      solarRadiationMjM2: 24,
      evapotranspirationMm: 2200,
    },
    topography: {
      slopePct: 3,
      aspectDeg: 180,
      elevationM: 1750,
      curvature: 'flat',
    },
    currentLandUse: 'orchard',
    ndvi: 0.55,
  },
];

export const LandLoader: React.FC<LandLoaderProps> = ({ onLandLoaded }) => {
  const [mode, setMode] = useState<'select' | 'custom'>('select');
  const [customCoords, setCustomCoords] = useState<LandBBox>({
    north: 35.5, south: 35.4, east: 51.5, west: 51.4,
  });

  return (
    <Card title="بارگذاری زمین" icon={<Globe size={20} />} subtitle="آزمایشگاه مجازی زمین شما">
      {/* Mode Selector */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <button
          onClick={() => setMode('select')}
          className={`btn ${mode === 'select' ? 'btn-primary' : 'btn-secondary'}`}
        >
          <MapPin size={16} /> انتخاب از نمونه‌ها
        </button>
        <button
          onClick={() => setMode('custom')}
          className={`btn ${mode === 'custom' ? 'btn-primary' : 'btn-secondary'}`}
        >
          <Globe size={16} /> مختصات سفارشی
        </button>
        <button className="btn btn-ghost">
          <Upload size={16} /> آپلود GeoJSON
        </button>
      </div>

      {mode === 'select' ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
          {SAMPLE_LANDS.map((land) => (
            <motion.div
              key={land.id}
              whileHover={{ scale: 1.02, y: -4 }}
              onClick={() => onLandLoaded(land)}
              className="card"
              style={{ cursor: 'pointer', padding: '1.5rem', border: '2px solid var(--color-border)' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <h4 style={{ margin: 0, fontSize: '1rem' }}>{land.name}</h4>
                <div style={{
                  padding: '0.25rem 0.5rem',
                  background: land.currentLandUse === 'bare' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(34, 197, 94, 0.1)',
                  color: land.currentLandUse === 'bare' ? 'var(--color-error)' : 'var(--color-success)',
                  borderRadius: 'var(--radius-full)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                }}>
                  {land.currentLandUse === 'bare' ? 'بایر' : land.currentLandUse === 'cropland' ? 'زراعی' : 'باغ'}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem', fontSize: '0.875rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Mountain size={14} color="var(--color-text-tertiary)" />
                  <span>{land.areaHa} هکتار</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Droplets size={14} color="var(--color-info)" />
                  <span>{land.climate.annualRainfallMm} mm/سال</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Thermometer size={14} color="var(--color-warning)" />
                  <span>{land.climate.avgTempC}°C</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '0.875rem' }}>📐</span>
                  <span>شیب {land.topography.slopePct}٪</span>
                </div>
              </div>

              <div style={{
                marginTop: '1rem',
                padding: '0.5rem',
                background: 'var(--color-surface)',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.75rem',
                color: 'var(--color-text-tertiary)',
              }}>
                NDVI فعلی: <strong style={{ color: land.ndvi > 0.4 ? 'var(--color-success)' : 'var(--color-warning)' }}>
                  {land.ndvi.toFixed(2)}
                </strong>
                {' '}| خاک: {land.soil.texture} | ارتفاع: {land.topography.elevationM}m
              </div>
            </motion.div>
          ))}
        </div>
      ) : (
        <div style={{ padding: '2rem', background: 'var(--color-surface)', borderRadius: 'var(--radius-lg)' }}>
          <h4 style={{ marginBottom: '1rem' }}>محدوده زمین را مشخص کنید</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
            {(['north', 'south', 'east', 'west'] as const).map((key) => (
              <div key={key}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                  {key === 'north' ? 'عرض شمالی' : key === 'south' ? 'عرض جنوبی' : key === 'east' ? 'طول شرقی' : 'طول غربی'}
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={customCoords[key]}
                  onChange={(e) => setCustomCoords({ ...customCoords, [key]: parseFloat(e.target.value) })}
                  className="input"
                />
              </div>
            ))}
          </div>
          <Button
            variant="primary"
            style={{ marginTop: '1.5rem', width: '100%' }}
            onClick={() => {
              // در production: فراخوانی API برای دریافت DEM + Soil + Climate
              onLandLoaded({
                id: 'custom-' + Date.now(),
                name: 'زمین سفارشی',
                bbox: customCoords,
                areaHa: 25,
                soil: { texture: 'loam', organicCarbonPct: 1.0, ph: 7.0, depthCm: 80, bulkDensity: 1.3, infiltrationRateMmHr: 20 },
                climate: { annualRainfallMm: 300, avgTempC: 18, maxTempC: 38, minTempC: -8, windSpeedMs: 6, windDirectionDeg: 270, solarRadiationMjM2: 20, evapotranspirationMm: 1200 },
                topography: { slopePct: 10, aspectDeg: 180, elevationM: 1500, curvature: 'flat' },
                currentLandUse: 'bare',
                ndvi: 0.3,
              });
            }}
          >
            بارگذاری زمین و شروع شبیه‌سازی
          </Button>
        </div>
      )}
    </Card>
  );
};
