'use client';
import { useState } from 'react';
import { useI18n } from '../lib/i18n-context';
import { API_BASE } from '../lib/config';
import backendTranslations from '../locales/backend_translations.json';

interface AnalysisResult {
  lat: number;
  lon: number;
  analysis_date: string;
  ndvi: number;
  evi: number;
  savi: number;
  ndwi: number;
  nbr: number;
  vegetation_status: {
    class: string;
    description: string;
  };
  cloud_cover: number;
  data_quality: string;
  recommendation: string;
}

export default function SatellitePanel() {
  const { t, locale } = useI18n();
  const [lat, setLat] = useState('36.8');
  const [lon, setLon] = useState('54.4');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Helper function to translate backend messages
  const translateBackendMessage = (messageKey: string, fallback: string): string => {
    const translations = backendTranslations as unknown as Record<string, Record<string, string>>;
    const translation = translations[messageKey];
    if (translation && translation[locale]) {
      return translation[locale];
    }
    return fallback;
  };

  // Map backend recommendation text to translation keys
  const getTranslatedRecommendation = (backendRecommendation: string): string => {
    const keyMap: Record<string, string> = {
      "Vegetation cover is sparse": "satellite.recommendation.sparse_vegetation",
      "Moderate vegetation detected": "satellite.recommendation.moderate_vegetation",
      "Excellent vegetation health": "satellite.recommendation.dense_vegetation",
      "Low moisture content detected": "satellite.recommendation.low_moisture",
      "Good water availability": "satellite.recommendation.good_water",
      "Soil is exposed to erosion": "satellite.recommendation.soil_exposed",
      "Conditions appear stable": "satellite.recommendation.stable",
      "Satellite data temporarily unavailable": "satellite.fallback.no_data",
    };

    for (const [pattern, key] of Object.entries(keyMap)) {
      if (backendRecommendation.includes(pattern)) {
        return translateBackendMessage(key, backendRecommendation);
      }
    }
    return backendRecommendation;
  };

  const analyze = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/satellite/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat: parseFloat(lat),
          lon: parseFloat(lon),
        }),
      });

      if (!res.ok) throw new Error('Analysis failed');
      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getIndexColor = (value: number, type: string): string => {
    if (type === 'ndvi') {
      if (value < 0.1) return '#dc2626';
      if (value < 0.3) return '#f59e0b';
      if (value < 0.5) return '#eab308';
      return '#16a34a';
    }
    if (type === 'ndwi') {
      return value > 0 ? '#2563eb' : '#dc2626';
    }
    return '#6b7280';
  };

  return (
    <section
      aria-labelledby="satellite-panel-title"
      style={{
        marginTop: '32px',
        padding: '24px',
        border: '1px solid #ddd',
        borderRadius: '12px',
        background: '#f0f9ff',
      }}
    >
      <h2 id="satellite-panel-title" style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '16px', color: '#0c4a6e' }}>
        🛰️ {t('satellite_title')}
      </h2>
      <p style={{ color: '#475569', marginBottom: '16px' }}>
        {t('satellite_subtitle')}
      </p>

      <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <div>
          <label htmlFor="sat-lat" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>{t('latitude')}</label>
          <input
            id="sat-lat"
            type="number"
            step="0.001"
            value={lat}
            onChange={(e) => setLat(e.target.value)}
            style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '6px', width: '120px' }}
          />
        </div>
        <div>
          <label htmlFor="sat-lon" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>{t('longitude')}</label>
          <input
            id="sat-lon"
            type="number"
            step="0.001"
            value={lon}
            onChange={(e) => setLon(e.target.value)}
            style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '6px', width: '120px' }}
          />
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-end' }}>
          <button
            onClick={analyze}
            disabled={loading}
            aria-busy={loading}
            style={{
              padding: '8px 24px',
              background: loading ? '#9ca3af' : '#0369a1',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? t('analyzing') : t('analyze_button')}
          </button>
        </div>
      </div>

      {error && <p role="alert" style={{ color: '#dc2626' }}>{t('error_label')}: {error}</p>}

      {loading && <p aria-live="polite" style={{ color: '#475569' }}>{t('analyzing')}</p>}

      {result && (
        <div
          aria-live="polite"
          style={{
            background: 'white',
            padding: '16px',
            borderRadius: '8px',
            marginTop: '16px',
          }}
        >
          <div style={{ marginBottom: '16px' }}>
            <strong>{t('analysis_date')}:</strong> {result.analysis_date} |
            <strong> {t('data_quality')}:</strong>{' '}
            <span style={{
              color: result.data_quality === 'good' ? '#16a34a' : result.data_quality === 'moderate' ? '#f59e0b' : '#dc2626'
            }}>
              {result.data_quality}
            </span> |
            <strong> {t('cloud_cover')}:</strong> {result.cloud_cover}%
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
            gap: '12px',
            marginBottom: '16px',
          }}>
            {[
              { label: t('vegetation'), value: result.ndvi, type: 'ndvi', name: 'NDVI' },
              { label: t('enhanced_veg'), value: result.evi, type: 'ndvi', name: 'EVI' },
              { label: t('soil_adjusted'), value: result.savi, type: 'ndvi', name: 'SAVI' },
              { label: t('water'), value: result.ndwi, type: 'ndwi', name: 'NDWI' },
              { label: t('burn_ratio'), value: result.nbr, type: 'default', name: 'NBR' },
            ].map((idx) => (
              <div key={idx.name} style={{
                padding: '12px',
                background: '#f8fafc',
                borderRadius: '6px',
                textAlign: 'center',
              }}>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{idx.label}</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: getIndexColor(idx.value, idx.type) }}>
                  {idx.value.toFixed(3)}
                </div>
                <div style={{ fontSize: '0.875rem', fontWeight: '600' }}>{idx.name}</div>
              </div>
            ))}
          </div>

          <div style={{
            padding: '12px',
            background: '#f1f5f9',
            borderRadius: '6px',
            marginBottom: '12px',
          }}>
            <strong>{t('status')}:</strong> {result.vegetation_status.description}
          </div>

          <div style={{
            padding: '12px',
            background: '#dcfce7',
            borderRadius: '6px',
            borderInlineStart: '4px solid #16a34a',
          }}>
            <strong>💡 {t('recommendation')}:</strong>
            <p style={{ margin: '8px 0 0 0' }}>{getTranslatedRecommendation(result.recommendation)}</p>
          </div>
        </div>
      )}
    </section>
  );
}
