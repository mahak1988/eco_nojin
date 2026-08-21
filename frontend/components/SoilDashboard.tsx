'use client';
import { useEffect, useState } from 'react';
import { useI18n } from '../lib/i18n-context';
import { API_BASE } from '../lib/config';

interface SoilProfile {
  id: number;
  name: string;
  texture: string | null;
  ph: number | null;
  ec: number | null;
  organic_matter: number | null;
}

export default function SoilDashboard() {
  const { t } = useI18n();
  const [soils, setSoils] = useState<SoilProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/soil/`)
      .then((res) => {
        if (!res.ok) throw new Error('Network response was not ok');
        return res.json();
      })
      .then((data) => {
        setSoils(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <p aria-live="polite" style={{ color: '#2563eb' }}>{t('loading_soil')}</p>;
  if (error) return <p role="alert" style={{ color: '#dc2626' }}>{t('error_label')}: {error}</p>;

  return (
    <section
      aria-live="polite"
      aria-labelledby="soil-dashboard-title"
      style={{ marginTop: '24px' }}
    >
      <h2 id="soil-dashboard-title" style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '16px' }}>{t('dashboard')}: {t('farmers')}</h2>
      {soils.length === 0 ? (
        <p>{t('no_soil_profiles')}</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
          {soils.map((soil) => (
            <div key={soil.id} style={{ padding: '16px', border: '1px solid #ddd', borderRadius: '8px', background: '#f9f9f9' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '8px' }}>{soil.name}</h3>
              <p><strong>{t('texture_label')}:</strong> {soil.texture || 'N/A'}</p>
              <p><strong>pH:</strong> {soil.ph ?? 'N/A'}</p>
              <p><strong>EC:</strong> {soil.ec ?? 'N/A'} dS/m</p>
              <p><strong>{t('organic_matter_label')}:</strong> {soil.organic_matter ?? 'N/A'}%</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
