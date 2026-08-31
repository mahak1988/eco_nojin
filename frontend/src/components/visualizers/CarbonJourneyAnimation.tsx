import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Leaf,
  Droplets,
  Cloud,
  Database,
  Coins,
  Shield,
  ArrowLeft,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { Card, Button } from '../ui';

/**
 * مراحل سفر کربن از خاک تا بلاکچین
 * این کامپوننت فلسفه HyDroMa را به کاربر منتقل می‌کند
 */
const JOURNEY_STEPS = [
  {
    id: 'soil',
    title: '🌱 خاک',
    titleFa: 'خاک زنده',
    description: 'گیاهان CO₂ را از اتمسفر جذب می‌کنند و در خاک ذخیره می‌کنند',
    scientificNote: 'RothC: کربن آلی خاک (SOC) در ۴ مخزن: DPM, RPM, BIO, HUM',
    icon: Leaf,
    color: '#10b981',
    value: '۱.۵ تن/هکتار در سال',
  },
  {
    id: 'water',
    title: '💧 آب',
    titleFa: 'چرخه آب',
    description: 'آب از طریق ریشه‌ها، کربن را در خاک تثبیت می‌کند',
    scientificNote: 'HyDroMa: نفوذ + تغذیه آبخوان = تقویت SOC',
    icon: Droplets,
    color: '#3b82f6',
    value: '۲۸۰ mm نفوذ',
  },
  {
    id: 'atmosphere',
    title: '☁️ اتمسفر',
    titleFa: 'هوای پاک',
    description: 'هر تن کربن = ۳.۶۷ تن CO₂ از اتمسفر حذف می‌شود',
    scientificNote: 'IPCC: ۴۴/۱۲ = ضریب تبدیل C به CO₂',
    icon: Cloud,
    color: '#06b6d4',
    value: '۵.۵ تن CO₂ حذف‌شده',
  },
  {
    id: 'mrv',
    title: '📊 MRV',
    titleFa: 'اندازه‌گیری و تأیید',
    description: 'ماهواره‌ها و IoT داده‌های واقعی را جمع‌آوری می‌کنند',
    scientificNote: 'Sentinel-2 NDVI + سنسورهای خاک + AI Validation',
    icon: Shield,
    color: '#8b5cf6',
    value: 'دقت ۹۲٪',
  },
  {
    id: 'blockchain',
    title: '🔗 بلاکچین',
    titleFa: 'ثبت غیرقابل تغییر',
    description: 'کربن تاییدشده روی Polygon به NFT تبدیل می‌شود',
    scientificNote: 'Smart Contract: CarbonCredit.sol (ERC-1155)',
    icon: Database,
    color: '#f59e0b',
    value: 'Token ID: #۲۰۲۶-۸۸',
  },
  {
    id: 'credit',
    title: '💰 اعتبار کربن',
    titleFa: 'درآمد پایدار',
    description: 'هر Credit = ۱ تن CO₂ قابل معامله در بازار جهانی',
    scientificNote: 'Verra VCS + Gold Standard = بازار $۴۰-۸۰/تن',
    icon: Coins,
    color: '#22c55e',
    value: '$۳۲۰ USDT',
  },
];

export const CarbonJourneyAnimation: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);

  useEffect(() => {
    if (!isAutoPlaying) return;
    const timer = setInterval(() => {
      setCurrentStep((prev) => (prev + 1) % JOURNEY_STEPS.length);
    }, 4000);
    return () => clearInterval(timer);
  }, [isAutoPlaying]);

  const step = JOURNEY_STEPS[currentStep];
  const Icon = step.icon;

  const next = () => setCurrentStep((prev) => (prev + 1) % JOURNEY_STEPS.length);
  const prev = () =>
    setCurrentStep((prev) => (prev - 1 + JOURNEY_STEPS.length) % JOURNEY_STEPS.length);

  return (
    <Card
      title="سفر کربن: از خاک تا بلاکچین"
      icon={<Sparkles size={20} />}
      subtitle="فلسفه HyDroMa در عمل"
    >
      {/* Progress Bar */}
      <div style={{ display: 'flex', gap: '0.25rem', marginBottom: '2rem' }}>
        {JOURNEY_STEPS.map((s, i) => (
          <motion.button
            key={s.id}
            onClick={() => {
              setCurrentStep(i);
              setIsAutoPlaying(false);
            }}
            whileHover={{ scale: 1.1 }}
            style={{
              flex: 1,
              height: 6,
              borderRadius: 3,
              border: 'none',
              cursor: 'pointer',
              background:
                i === currentStep
                  ? s.color
                  : i < currentStep
                    ? `${s.color}80`
                    : 'var(--color-border)',
              transition: 'all 0.3s',
            }}
          />
        ))}
      </div>

      {/* Current Step */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -50 }}
          transition={{ duration: 0.4 }}
          style={{
            textAlign: 'center',
            padding: '2rem 1rem',
            background: `linear-gradient(135deg, ${step.color}15, ${step.color}05)`,
            borderRadius: 'var(--radius-xl)',
            border: `2px solid ${step.color}40`,
            marginBottom: '1.5rem',
          }}
        >
          <motion.div
            animate={{ rotate: [0, 10, -10, 0], scale: [1, 1.1, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            style={{
              width: 80,
              height: 80,
              borderRadius: '50%',
              background: `${step.color}20`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1rem',
              color: step.color,
            }}
          >
            <Icon size={40} />
          </motion.div>

          <h3 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            {step.titleFa}
          </h3>
          <p
            style={{
              fontSize: '1.125rem',
              color: 'var(--color-text-secondary)',
              marginBottom: '1rem',
              lineHeight: 1.8,
            }}
          >
            {step.description}
          </p>

          <div
            style={{
              display: 'inline-block',
              padding: '0.5rem 1rem',
              background: `${step.color}20`,
              color: step.color,
              borderRadius: 'var(--radius-full)',
              fontWeight: 600,
              marginBottom: '1rem',
            }}
          >
            {step.value}
          </div>

          <div
            style={{
              marginTop: '1rem',
              padding: '0.75rem',
              background: 'var(--color-surface)',
              borderRadius: 'var(--radius-lg)',
              fontSize: '0.875rem',
              color: 'var(--color-text-secondary)',
              fontFamily: 'monospace',
              textAlign: 'left',
            }}
          >
            <strong>🔬 {step.scientificNote}</strong>
          </div>
        </motion.div>
      </AnimatePresence>

      {/* Navigation */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Button variant="ghost" onClick={prev} icon={<ArrowRight size={16} />}>
          قبلی
        </Button>

        <div style={{ display: 'flex', gap: '0.5rem', fontSize: '0.875rem' }}>
          <span style={{ color: 'var(--color-text-tertiary)' }}>
            مرحله {currentStep + 1} از {JOURNEY_STEPS.length}
          </span>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <Button variant="ghost" onClick={() => setIsAutoPlaying(!isAutoPlaying)}>
            {isAutoPlaying ? '⏸' : '▶'}
          </Button>
          <Button variant="primary" onClick={next} icon={<ArrowLeft size={16} />}>
            بعدی
          </Button>
        </div>
      </div>
    </Card>
  );
};
