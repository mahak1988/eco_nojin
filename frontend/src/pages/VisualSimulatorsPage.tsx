import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Wind, Droplets, Sprout, Sparkles, Map } from 'lucide-react';
import { AppLayout } from '../components/layout/AppLayout';
import { Card, Tabs } from '../components/ui';
import {
  WindSimulation2D,
  WaterInfiltration3D,
  WatershedFlowMap,
  CarbonJourneyAnimation,
  MultiLayerFarm3D,
  HyDroMaPhilosophyHub,
} from '../components/visualizers';

export const VisualSimulatorsPage: React.FC = () => {
  const [soilTexture, setSoilTexture] = useState<'sand' | 'loam' | 'clay'>('loam');

  const tabs = [
    {
      id: 'philosophy',
      label: '🌍 فلسفه HyDroMa',
      icon: <Sparkles size={16} />,
      content: (
        <div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              textAlign: 'center',
              padding: '2rem',
              background: 'linear-gradient(135deg, var(--color-primary), var(--color-info))',
              borderRadius: 'var(--radius-2xl)',
              color: 'white',
              marginBottom: '2rem',
            }}
          >
            <h1 style={{ fontSize: '2.5rem', fontWeight: 800, marginBottom: '0.5rem' }}>
              از قطره تا اقیانوس
            </h1>
            <p style={{ fontSize: '1.5rem', fontWeight: 300, margin: 0 }}>از دانه تا جنگل</p>
          </motion.div>
          <HyDroMaPhilosophyHub />
          <div style={{ marginTop: '2rem' }}>
            <CarbonJourneyAnimation />
          </div>
        </div>
      ),
    },
    {
      id: 'wind',
      label: '🌬️ باد و فرسایش',
      icon: <Wind size={16} />,
      content: (
        <WindSimulation2D
          width={900}
          height={450}
          windSpeed={12}
          onErosionCalculated={(e) => console.log('Erosion:', e)}
        />
      ),
    },
    {
      id: 'water',
      label: '💧 نفوذ آب',
      icon: <Droplets size={16} />,
      content: (
        <Card title="شبیه‌سازی نفوذ آب در خاک" icon={<Droplets size={20} />}>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
            {(['sand', 'loam', 'clay'] as const).map((tex) => (
              <button
                key={tex}
                onClick={() => setSoilTexture(tex)}
                className={`btn ${soilTexture === tex ? 'btn-primary' : 'btn-secondary'}`}
              >
                {tex === 'sand' ? 'شنی' : tex === 'loam' ? 'لومی' : 'رسی'}
              </button>
            ))}
          </div>
          <WaterInfiltration3D soilTexture={soilTexture} rainfallIntensity={40} />
          <div
            style={{
              marginTop: '1rem',
              padding: '1rem',
              background: 'var(--color-surface)',
              borderRadius: 'var(--radius-lg)',
              fontSize: '0.875rem',
              lineHeight: 1.8,
            }}
          >
            <strong>💡 Green-Ampt Model:</strong> نفوذ آب به خاک با معادله Green-Ampt محاسبه می‌شود:
            <br />
            <code
              style={{
                fontFamily: 'monospace',
                direction: 'ltr',
                display: 'block',
                marginTop: '0.5rem',
              }}
            >
              f = Ks × (1 + (ψ × Δθ) / F)
            </code>
          </div>
        </Card>
      ),
    },
    {
      id: 'watershed',
      label: '🗺️ حوضه آبخیز',
      icon: <Map size={16} />,
      content: (
        <Card title="نقشه جریان آب در حوضه آبخیز" icon={<Map size={20} />}>
          <WatershedFlowMap center={[51.4, 35.5]} zoom={10} />
          <div
            style={{
              marginTop: '1rem',
              padding: '1rem',
              background: 'var(--color-surface)',
              borderRadius: 'var(--radius-lg)',
              fontSize: '0.875rem',
              lineHeight: 1.8,
            }}
          >
            <strong>💡 SCS Curve Number:</strong> مدل SCS-CN برای محاسبه رواناب:
            <br />
            <code
              style={{
                fontFamily: 'monospace',
                direction: 'ltr',
                display: 'block',
                marginTop: '0.5rem',
              }}
            >
              Q = (P - 0.2S)² / (P + 0.8S) where S = (25400/CN) - 254
            </code>
          </div>
        </Card>
      ),
    },
    {
      id: 'farm',
      label: '🌾 کشت چندلایه',
      icon: <Sprout size={16} />,
      content: (
        <Card title="مزرعه سه‌بعدی چندلایه" icon={<Sprout size={20} />}>
          <MultiLayerFarm3D
            showCanopy={true}
            showSubCanopy={true}
            showGround={true}
            showAnimals={true}
          />
          <div
            style={{
              marginTop: '1rem',
              padding: '1rem',
              background: 'var(--color-surface)',
              borderRadius: 'var(--radius-lg)',
              fontSize: '0.875rem',
              lineHeight: 1.8,
            }}
          >
            <strong>🌿 Agroforestry Benefits:</strong>
            <ul style={{ margin: '0.5rem 0 0 0', paddingRight: '1.25rem' }}>
              <li>
                افزایش عملکرد کل: <strong>۲۵٪</strong> نسبت به تک‌کشتی
              </li>
              <li>
                کاهش مصرف آب: <strong>۳۰٪</strong> با سایه‌اندازی
              </li>
              <li>
                افزایش تنوع زیستی: <strong>۳ برابر</strong>
              </li>
              <li>
                کربن ذخیره‌شده: <strong>۲.۵ تن/هکتار/سال</strong>
              </li>
            </ul>
          </div>
        </Card>
      ),
    },
  ];

  return (
    <AppLayout>
      <div style={{ maxWidth: 1600, margin: '0 auto', padding: '2rem' }}>
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ marginBottom: '2rem' }}
        >
          <h1 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            🎨 شبیه‌سازهای بصری اکوسیستم
          </h1>
          <p style={{ color: 'var(--color-text-secondary)' }}>
            نمایش علمی پدیده‌های طبیعی و اقتصادی در قالب شبیه‌سازی‌های تعاملی
          </p>
        </motion.div>

        <Tabs tabs={tabs} defaultTab="philosophy" variant="pills" />
      </div>
    </AppLayout>
  );
};
