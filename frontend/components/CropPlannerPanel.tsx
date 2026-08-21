'use client';
import { useState } from 'react';
import { useI18n } from '../lib/i18n-context';
import { API_BASE } from '../lib/config';

interface CropSimulation {
  crop: string;
  actual_yield_kg_ha: number;
  gross_revenue_usd_ha: number;
  water_stress_factor: number;
  temp_stress_factor: number;
  co2_fertilization: number;
}

export default function CropPlannerPanel() {
  const { t } = useI18n();
  const [result, setResult] = useState<CropSimulation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [cropType, setCropType] = useState('wheat');
  const [availableWater, setAvailableWater] = useState(350);
  const [meanTemp, setMeanTemp] = useState(22);
  const [co2, setCo2] = useState(420);

  const simulate = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/scenarios/crop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          crop_type: cropType,
          available_water: availableWater,
          mean_temp: meanTemp,
          co2_concentration: co2,
        }),
      });

      if (!res.ok) throw new Error('Simulation failed');
      setResult(await res.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section
      aria-labelledby="crop-planner-title"
      style={{
        marginTop: '32px',
        padding: '24px',
        border: '1px solid #ddd',
        borderRadius: '12px',
        background: '#dcfce7',
      }}
    >
      <h2 id="crop-planner-title" style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '16px', color: '#166534' }}>
        🌾 {t('crop_planner_title')}
      </h2>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px', marginBottom: '16px' }}>
        <div>
          <label htmlFor="crop-type" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>Crop</label>
          <select
            id="crop-type"
            value={cropType}
            onChange={(e) => setCropType(e.target.value)}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '6px' }}
          >
            <option value="wheat">Wheat</option>
            <option value="barley">Barley</option>
            <option value="corn">Corn</option>
            <option value="millet">Millet</option>
            <option value="sorghum">Sorghum</option>
            <option value="chickpea">Chickpea</option>
            <option value="safflower">Safflower</option>
            <option value="medicinal_herbs">Medicinal Herbs</option>
          </select>
        </div>

        <div>
          <label htmlFor="crop-water" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>Water (mm)</label>
          <input
            id="crop-water"
            type="number"
            value={availableWater}
            onChange={(e) => setAvailableWater(parseFloat(e.target.value))}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '6px' }}
          />
        </div>

        <div>
          <label htmlFor="crop-temp" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>Temp (°C)</label>
          <input
            id="crop-temp"
            type="number"
            value={meanTemp}
            onChange={(e) => setMeanTemp(parseFloat(e.target.value))}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '6px' }}
          />
        </div>

        <div>
          <label htmlFor="crop-co2" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>CO₂ (ppm)</label>
          <input
            id="crop-co2"
            type="number"
            value={co2}
            onChange={(e) => setCo2(parseFloat(e.target.value))}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '6px' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'flex-end' }}>
          <button
            onClick={simulate}
            disabled={loading}
            aria-busy={loading}
            style={{ padding: '10px 24px', background: '#166534', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', width: '100%' }}
          >
            {loading ? t('analyzing') : t('simulate_yield')}
          </button>
        </div>
      </div>

      {error && <p role="alert" style={{ color: '#dc2626' }}>{t('error_label')}: {error}</p>}

      {result && (
        <div aria-live="polite" style={{ background: 'white', padding: '16px', borderRadius: '8px', marginTop: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '12px' }}>
            {result.crop} - {t('results')}
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
            <div style={{ padding: '12px', background: '#f0fdf4', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#166534' }}>
                {result.actual_yield_kg_ha.toLocaleString()}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#4b5563' }}>{t('yield_kg_ha')}</div>
            </div>

            <div style={{ padding: '12px', background: '#fef3c7', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#92400e' }}>
                ${result.gross_revenue_usd_ha.toLocaleString()}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#4b5563' }}>{t('revenue_usd_ha')}</div>
            </div>

            <div style={{ padding: '12px', background: '#dbeafe', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1e40af' }}>
                {(result.water_stress_factor * 100).toFixed(0)}%
              </div>
              <div style={{ fontSize: '0.875rem', color: '#4b5563' }}>{t('water_factor')}</div>
            </div>

            <div style={{ padding: '12px', background: '#fce7f3', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#9d174d' }}>
                {(result.temp_stress_factor * 100).toFixed(0)}%
              </div>
              <div style={{ fontSize: '0.875rem', color: '#4b5563' }}>{t('temp_factor')}</div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
