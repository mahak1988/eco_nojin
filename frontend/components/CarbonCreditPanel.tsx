'use client';
import { useState } from 'react';
import { useI18n } from '../lib/i18n-context';
import { API_BASE } from '../lib/config';

interface CarbonResult {
  project_type: string;
  annual_rate_tonnes: number;
  total_carbon_tonnes: number;
  total_carbon_min: number;
  total_carbon_max: number;
  estimated_revenue_usd: number;
  annual_revenue_usd: number;
  permanence_years: number;
  methodology: string;
}

export default function CarbonCreditPanel() {
  const { t } = useI18n();
  const [result, setResult] = useState<CarbonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [projectType, setProjectType] = useState('afforestation');
  const [areaHa, setAreaHa] = useState(100);
  const [durationYears, setDurationYears] = useState(10);
  const [region, setRegion] = useState('temperate');

  const calculate = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/carbon/calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_type: projectType,
          area_ha: areaHa,
          duration_years: durationYears,
          region: region,
        }),
      });

      if (!res.ok) throw new Error('Carbon calculation failed');
      setResult(await res.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const projectTypes = [
    { value: 'afforestation', label: 'Afforestation', rate: 8.0 },
    { value: 'reforestation', label: 'Reforestation', rate: 6.0 },
    { value: 'soil_carbon_no_till', label: 'Soil Carbon (No-Till)', rate: 0.8 },
    { value: 'soil_carbon_cover_crop', label: 'Soil Carbon (Cover Crop)', rate: 0.5 },
    { value: 'soil_carbon_compost', label: 'Soil Carbon (Compost)', rate: 1.2 },
    { value: 'biochar', label: 'Biochar', rate: 3.0 },
    { value: 'agroforestry', label: 'Agroforestry', rate: 4.5 },
    { value: 'grassland_restoration', label: 'Grassland Restoration', rate: 1.5 },
  ];

  return (
    <section
      aria-labelledby="carbon-panel-title"
      style={{
        marginTop: '32px',
        padding: '24px',
        border: '1px solid #ddd',
        borderRadius: '12px',
        background: '#d1fae5',
      }}
    >
      <h2 id="carbon-panel-title" style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '16px', color: '#065f46' }}>
        🌱 {t('carbon_title')}
      </h2>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px', marginBottom: '16px' }}>
        <div>
          <label htmlFor="carbon-type" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>{t('project_type')}</label>
          <select
            id="carbon-type"
            value={projectType}
            onChange={(e) => setProjectType(e.target.value)}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '6px' }}
          >
            {projectTypes.map(pt => (
              <option key={pt.value} value={pt.value}>
                {pt.label} ({pt.rate} t/ha/yr)
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="carbon-area" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>{t('area_ha')}</label>
          <input
            id="carbon-area"
            type="number"
            value={areaHa}
            onChange={(e) => setAreaHa(parseFloat(e.target.value))}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '6px' }}
          />
        </div>

        <div>
          <label htmlFor="carbon-duration" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>{t('duration_years')}</label>
          <input
            id="carbon-duration"
            type="number"
            value={durationYears}
            onChange={(e) => setDurationYears(parseInt(e.target.value))}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '6px' }}
          />
        </div>

        <div>
          <label htmlFor="carbon-region" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>Region</label>
          <select
            id="carbon-region"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '6px' }}
          >
            <option value="tropical">Tropical</option>
            <option value="temperate">Temperate</option>
            <option value="arid">Arid</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'flex-end' }}>
          <button
            onClick={calculate}
            disabled={loading}
            aria-busy={loading}
            style={{ padding: '10px 24px', background: '#065f46', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', width: '100%' }}
          >
            {loading ? t('analyzing') : t('calculate_carbon')}
          </button>
        </div>
      </div>

      {error && <p role="alert" style={{ color: '#dc2626' }}>{t('error_label')}: {error}</p>}

      {result && (
        <div aria-live="polite" style={{ background: 'white', padding: '16px', borderRadius: '8px', marginTop: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '12px' }}>
            {t('results')}
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
            <div style={{ padding: '12px', background: '#ecfdf5', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#065f46' }}>
                {result.total_carbon_tonnes.toLocaleString()}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#4b5563' }}>{t('total_carbon')} (t CO₂)</div>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
                Range: {result.total_carbon_min.toLocaleString()} - {result.total_carbon_max.toLocaleString()}
              </div>
            </div>

            <div style={{ padding: '12px', background: '#fef3c7', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#92400e' }}>
                ${result.estimated_revenue_usd.toLocaleString()}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#4b5563' }}>Estimated Revenue</div>
            </div>

            <div style={{ padding: '12px', background: '#dbeafe', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1e40af' }}>
                {result.annual_rate_tonnes.toFixed(1)}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#4b5563' }}>{t('annual_rate')} (t CO₂/yr)</div>
            </div>

            <div style={{ padding: '12px', background: '#fce7f3', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#9d174d' }}>
                {result.permanence_years}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#4b5563' }}>Permanence (years)</div>
            </div>
          </div>

          <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '12px' }}>
            Methodology: {result.methodology}
          </p>
        </div>
      )}
    </section>
  );
}
