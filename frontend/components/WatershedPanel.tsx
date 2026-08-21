'use client';
import { useState } from 'react';
import { useI18n } from '../lib/i18n-context';
import { API_BASE } from '../lib/config';

export default function WatershedPanel() {
  const { t } = useI18n();
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [structureType, setStructureType] = useState('check_dam');
  const [slopePct, setSlopePct] = useState(15);
  const [areaM2, setAreaM2] = useState(10000);
  const [rainfallMm, setRainfallMm] = useState(100);

  const calculate = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/watershed/design`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          structure_type: structureType,
          slope_pct: slopePct,
          area_m2: areaM2,
          rainfall_mm: rainfallMm,
        }),
      });

      if (!res.ok) throw new Error('Design calculation failed');
      setResult(await res.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const structureTypes = [
    { value: 'check_dam', label: `🧱 ${t('check_dam')}` },
    { value: 'contour_trench', label: `📏 ${t('contour_trench')}` },
    { value: 'half_moon', label: `🌙 ${t('half_moon')}` },
    { value: 'terrace', label: `🏞️ ${t('terrace')}` },
    { value: 'gully_plug', label: '🪨 Gully Plug' },
  ];

  return (
    <section
      aria-labelledby="watershed-panel-title"
      style={{
        marginTop: '32px',
        padding: '24px',
        border: '1px solid #ddd',
        borderRadius: '12px',
        background: '#e0f2fe',
      }}
    >
      <h2 id="watershed-panel-title" style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '16px', color: '#0c4a6e' }}>
        🏗️ {t('watershed_title')}
      </h2>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px', marginBottom: '16px' }}>
        <div>
          <label htmlFor="ws-type" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>Structure Type</label>
          <select
            id="ws-type"
            value={structureType}
            onChange={(e) => setStructureType(e.target.value)}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '6px' }}
          >
            {structureTypes.map(st => (
              <option key={st.value} value={st.value}>{st.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="ws-slope" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>{t('slope_pct')}</label>
          <input
            id="ws-slope"
            type="number"
            value={slopePct}
            onChange={(e) => setSlopePct(parseFloat(e.target.value))}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '6px' }}
          />
        </div>

        <div>
          <label htmlFor="ws-area" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>{t('area_m2')}</label>
          <input
            id="ws-area"
            type="number"
            value={areaM2}
            onChange={(e) => setAreaM2(parseFloat(e.target.value))}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '6px' }}
          />
        </div>

        <div>
          <label htmlFor="ws-rain" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>{t('rainfall_mm')}</label>
          <input
            id="ws-rain"
            type="number"
            value={rainfallMm}
            onChange={(e) => setRainfallMm(parseFloat(e.target.value))}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '6px' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'flex-end' }}>
          <button
            onClick={calculate}
            disabled={loading}
            aria-busy={loading}
            style={{ padding: '10px 24px', background: '#0c4a6e', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', width: '100%' }}
          >
            {loading ? t('analyzing') : t('calculate_structure')}
          </button>
        </div>
      </div>

      {error && <p role="alert" style={{ color: '#dc2626' }}>{t('error_label')}: {error}</p>}

      {result && (
        <div aria-live="polite" style={{ background: 'white', padding: '16px', borderRadius: '8px', marginTop: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '12px' }}>
            {t('results')}: {result.structure_type}
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px' }}>
            {Object.entries(result).filter(([key, val]) =>
              typeof val === 'number' && !['slope_pct', 'area_m2', 'rainfall_mm'].includes(key)
            ).map(([key, val]) => {
              const num = val as number;
              return (
                <div key={key} style={{ padding: '12px', background: '#f0f9ff', borderRadius: '6px', textAlign: 'center' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#0c4a6e' }}>
                    {num.toLocaleString()}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#4b5563' }}>
                    {key.replace(/_/g, ' ')}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </section>
  );
}
