"use client";
import { useState } from 'react';
import Footer from '../../../components/layout/Footer';
import ScenarioComparison from '../../../components/charts/ScenarioComparison';
import { useI18n } from '../../../lib/i18n-context';
import { useTheme } from '../../../lib/theme-context';
import { motion } from 'framer-motion';
import { TrendingUp, AlertTriangle } from 'lucide-react';

export default function ScenariosPage() {
  const { t, direction } = useI18n();
  const { colors } = useTheme();
  const [baseline, setBaseline] = useState({ temp: 18.5, precip: 380 });

  return (
    <div dir={direction} style={{ background: colors.bg, minHeight: '100vh' }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '32px 20px' }}>
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{
            background: `linear-gradient(135deg, ${colors.warm}, ${colors.primary})`,
            padding: '32px', borderRadius: '24px', color: 'white',
            marginBottom: '32px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <TrendingUp size={40} />
            <div>
              <h1 style={{ fontSize: '2rem', fontWeight: '800', margin: 0 }}>{t('module_scenarios')}</h1>
              <p style={{ margin: '4px 0 0', opacity: 0.95 }}>
                {t('scenario_subtitle')}
              </p>
            </div>
          </div>
        </motion.div>

        {/* Baseline Controls */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{
            background: colors.cardBg, padding: '24px', borderRadius: '20px',
            border: `1px solid ${colors.border}`, marginBottom: '24px',
          }}
        >
          <h3 style={{ color: colors.text, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={20} color={colors.warm} />
            {t('scenario_baseline')}
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div>
              <label style={{ fontSize: '0.85rem', color: colors.textMuted, display: 'block', marginBottom: '6px' }}>
                {t('scenario_temp_label')}: <strong>{baseline.temp.toFixed(1)}°C</strong>
              </label>
              <input type="range" aria-label={t('scenario_temp_label')} min="-10" max="35" step="0.5"
                value={baseline.temp}
                onChange={(e) => setBaseline({ ...baseline, temp: parseFloat(e.target.value) })}
                style={{ width: '100%' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: colors.textMuted }}>
                <span>-10°C</span><span>35°C</span>
              </div>
            </div>
            <div>
              <label style={{ fontSize: '0.85rem', color: colors.textMuted, display: 'block', marginBottom: '6px' }}>
                Mean {t('scenario_precip_label')}: <strong>{baseline.precip}mm</strong>
              </label>
              <input type="range" aria-label={t('scenario_precip_label')} min="50" max="2500" step="10"
                value={baseline.precip}
                onChange={(e) => setBaseline({ ...baseline, precip: parseInt(e.target.value) })}
                style={{ width: '100%' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: colors.textMuted }}>
                <span>50mm (Arid)</span><span>2500mm (Tropical)</span>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Comparison */}
        <ScenarioComparison baselineTemp={baseline.temp} baselinePrecip={baseline.precip} />
      </div>
      <Footer />
    </div>
  );
}
