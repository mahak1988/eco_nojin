"use client";
import Footer from '../../../components/layout/Footer';
import ErosionRiskMap from '../../../components/maps/ErosionRiskMap';
import { useI18n } from '../../../lib/i18n-context';
import { useTheme } from '../../../lib/theme-context';
import { useFarm } from '../../../lib/farm-context';
import { motion } from 'framer-motion';
import { Mountain } from 'lucide-react';

export default function ErosionPage() {
  const { t, direction } = useI18n();
  const { colors } = useTheme();
  const { selectedFarm } = useFarm();

  const lat = selectedFarm?.latitude || 35.6892;
  const lon = selectedFarm?.longitude || 51.3890;

  return (
    <div dir={direction} style={{ background: colors.bg, minHeight: '100vh' }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '32px 20px' }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{
            background: `linear-gradient(135deg, ${colors.warm}, ${colors.danger})`,
            padding: '32px', borderRadius: '24px', color: 'white',
            marginBottom: '32px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <Mountain size={40} />
            <div>
              <h1 style={{ fontSize: '2rem', fontWeight: '800', margin: 0 }}>Soil Erosion Risk</h1>
              <p style={{ margin: '4px 0 0', opacity: 0.95 }}>
                RUSLE-based spatial analysis with C++ accelerated calculations
              </p>
            </div>
          </div>
        </motion.div>

        <ErosionRiskMap baseLat={lat} baseLon={lon} />
      </div>
      <Footer />
    </div>
  );
}
