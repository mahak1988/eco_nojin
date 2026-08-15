'use client';
import { useState } from 'react';
import Navbar from '../../../components/layout/Navbar';
import Footer from '../../../components/layout/Footer';
import { useI18n } from '../../../lib/i18n-context';
import { useTheme } from '../../../lib/theme-context';
import { motion } from 'framer-motion';
import { Droplet, Ruler } from 'lucide-react';
import { api } from '../../../lib/api-client';
import { LoadingState, ErrorState } from '../../../components/shared/ApiState';

export default function WatershedModulePage() {
  const { t, direction } = useI18n();
  const { colors } = useTheme();
  const [params, setParams] = useState({
    structure_type: 'check_dam',
    slope_percent: 10, catchment_area_ha: 50,
    rainfall_intensity_mmh: 30, soil_type: 'loam',
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const design = async () => {
    setLoading(true);
    setError(null);
    const res = await api.post<any>('/api/v1/watershed/design', params);
    if (res.success) setResult(res.data);
    else setError(res.error || 'Design failed');
    console.error('Watershed design error:', res.error);
    setLoading(false);
  };

  return (
    <div dir={direction} style={{ background: colors.bg, minHeight: '100vh' }}>
      <Navbar />
      <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '40px 20px' }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{
            background: 'linear-gradient(135deg, #38bdf8, #0284c7)',
            padding: '40px', borderRadius: '20px', color: 'white', marginBottom: '32px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <Droplet size={40} />
            <div>
              <h1 style={{ fontSize: '2rem', fontWeight: '800', margin: 0 }}>{t('module_watershed')}</h1>
              <p style={{ margin: '4px 0 0', opacity: 0.95 }}>{t('module_watershed_desc')}</p>
            </div>
          </div>
        </motion.div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          <div style={{ background: colors.cardBg, padding: '24px', borderRadius: '16px', border: `1px solid ${colors.border}` }}>
            <h3 style={{ marginBottom: '16px', color: colors.text }}>⚙️ Design Parameters</h3>
            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: colors.textMuted, marginBottom: '4px' }}>Structure Type</label>
              <select value={params.structure_type}
                onChange={(e) => setParams({ ...params, structure_type: e.target.value })}
                style={{ width: '100%', padding: '10px', borderRadius: '8px', border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text }}>
                <option value="check_dam">Check Dam</option>
                <option value="contour_trench">Contour Trench</option>
                <option value="half_moon">Half-Moon</option>
                <option value="gabion">Gabion</option>
              </select>
            </div>
            {[
              { k: 'slope_percent', label: 'Slope (%)', step: 1 },
              { k: 'catchment_area_ha', label: 'Catchment Area (ha)', step: 1 },
              { k: 'rainfall_intensity_mmh', label: 'Rainfall Intensity (mm/h)', step: 1 },
            ].map(({ k, label, step }) => (
              <div key={k} style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', color: colors.textMuted, marginBottom: '4px' }}>{label}</label>
                <input type="number" step={step} value={(params as any)[k]}
                  onChange={(e) => setParams({ ...params, [k]: parseFloat(e.target.value) || 0 })}
                  style={{ width: '100%', padding: '10px', borderRadius: '8px', border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text }} />
              </div>
            ))}
            <motion.button
              whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
              onClick={design} disabled={loading}
              style={{
                width: '100%', padding: '12px',
                background: 'linear-gradient(135deg, #38bdf8, #0284c7)',
                color: 'white', border: 'none', borderRadius: '10px',
                fontWeight: '600', cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
              }}
            >
              <Ruler size={18} /> Design Structure
            </motion.button>
          </div>

          <div>
            {loading && <LoadingState message="Designing structure..." />}
            {error && <ErrorState message={error} />}
            {result && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                style={{ background: colors.cardBg, padding: '24px', borderRadius: '16px', border: `1px solid ${colors.border}` }}>
                <h3 style={{ marginBottom: '16px', color: colors.text }}>📐 Design Specifications</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {Object.entries(result).map(([k, v]) => (
                    <div key={k} style={{
                      display: 'flex', justifyContent: 'space-between',
                      padding: '10px 12px', background: colors.bg, borderRadius: '8px',
                    }}>
                      <span style={{ color: colors.textMuted, fontSize: '0.9rem' }}>{k}</span>
                      <span style={{ fontWeight: '600', color: colors.accent }}>
                        {typeof v === 'number' ? v.toFixed(2) : String(v)}
                      </span>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}
