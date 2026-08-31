import React from 'react';
import { motion } from 'framer-motion';
import { FlaskConical } from 'lucide-react';
import { AppLayout } from '../components/layout/AppLayout';
import { ScientificHub } from '../components/simulators/ScientificHub';

/**
 * شبیه‌ساز دیجیتال مزرعه — بازسازی‌شده با موتورهای علمی واقعی (فاز ۲/۳).
 * صفحات و چارت‌های نمایشی قدیمی با داده ثابت حذف شدند؛ همه خروجی‌ها از زنجیره واقعی
 * (RUSLE ← SWAT+ ← Pywr ← RothC ← AquaCrop ← HEC-RAS ← NSGA-II) با داده ERA5/SoilGrids می‌آیند.
 */
export const SimulatorDashboard: React.FC = () => {
  return (
    <AppLayout>
      <div style={{ maxWidth: 1600, margin: '0 auto' }}>
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ marginBottom: '1.5rem' }}
        >
          <h1
            style={{
              fontSize: '1.8rem',
              fontWeight: 700,
              marginBottom: '0.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.6rem',
            }}
          >
            <FlaskConical size={26} color="var(--color-primary)" />
            شبیه‌سازهای علمی HyDroMa
          </h1>
          <p style={{ color: 'var(--color-text-secondary)', margin: 0 }}>
            زنجیره واقعی مدل‌ها: فرسایش (RUSLE) · کربن (RothC-26.3) · محصول (AquaCrop-OSPy) · آب
            (Pywr) · سیلاب (HEC-RAS) · بهینه‌سازی (NSGA-II) — با اقلیم ERA5 و خاک SoilGrids. هیچ
            خروجی ساختگی نمایش داده نمی‌شود.
          </p>
        </motion.div>

        <ScientificHub />
      </div>
    </AppLayout>
  );
};
