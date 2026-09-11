import { motion, useReducedMotion } from 'framer-motion';
import { Satellite, FileBarChart, ShieldCheck } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';

interface MrvStep {
  id: string;
  title: string;
  desc: string;
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  color: string;
}

const STEPS_FA: MrvStep[] = [
  {
    id: 'measure',
    title: 'اندازه‌گیری',
    desc: 'دادهٔ ماهواره‌ای (Sentinel-2، ERA5) + ثبت میدانی KoBo',
    icon: Satellite,
    color: 'var(--color-leaf-500)',
  },
  {
    id: 'report',
    title: 'گزارش',
    desc: 'خروجی MRV شفاف مبتنی بر ISO 14064-2',
    icon: FileBarChart,
    color: 'var(--color-aqua-500)',
  },
  {
    id: 'verify',
    title: 'راستی‌آزمایی',
    desc: 'بازبینی مستقل و ثبت بر روی بلاکچین',
    icon: ShieldCheck,
    color: 'var(--color-sand-500)',
  },
];

const STEPS_EN: MrvStep[] = [
  {
    id: 'measure',
    title: 'Measure',
    desc: 'Satellite data (Sentinel-2, ERA5) + KoBo field records',
    icon: Satellite,
    color: 'var(--color-leaf-500)',
  },
  {
    id: 'report',
    title: 'Report',
    desc: 'Transparent MRV output per ISO 14064-2',
    icon: FileBarChart,
    color: 'var(--color-aqua-500)',
  },
  {
    id: 'verify',
    title: 'Verify',
    desc: 'Independent review + blockchain registration',
    icon: ShieldCheck,
    color: 'var(--color-sand-500)',
  },
];

/** Animated MRV cycle: Measurement → Reporting → Verification (ISO 14064-2). */
export default function MrvCycleChart() {
  const { t, lang } = useLang();
  const reduce = useReducedMotion();
  const steps = lang === 'fa' ? STEPS_FA : STEPS_EN;

  return (
    <section className="px-4 py-12 sm:px-6">
      <Reveal className="mx-auto flex max-w-4xl flex-col items-center gap-6 text-center">
        <h2 className="text-2xl font-extrabold text-[var(--color-night-100)] sm:text-3xl">
          {t.impact.mrvCycle.title}
        </h2>
        <p className="max-w-2xl text-sm leading-7 text-[var(--color-night-200)]/65">
          {t.impact.mrvCycle.desc}
        </p>

        <div className="relative flex h-64 w-full max-w-3xl items-center justify-center">
          {/* orbit ring */}
          <motion.div
            className="absolute h-56 w-56 rounded-full border-2 border-dashed border-[var(--color-leaf-500)]/20"
            animate={
              reduce
                ? undefined
                : { rotate: 360 }
            }
            transition={{ duration: 40, repeat: Infinity, ease: 'linear' }}
            aria-hidden
          />
          <motion.div
            className="absolute h-40 w-40 rounded-full border border-[var(--color-aqua-500)]/15"
            animate={
              reduce
                ? undefined
                : { rotate: -360 }
            }
            transition={{ duration: 24, repeat: Infinity, ease: 'linear' }}
            aria-hidden
          />

          {/* step nodes positioned on circle */}
          {steps.map((step, index) => {
            const angle = (index * 120 - 90) * (Math.PI / 180);
            const radius = 96;
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;
            const Icon = step.icon;

            return (
              <motion.div
                key={step.id}
                className="absolute flex flex-col items-center gap-2"
                style={{
                  left: `calc(50% + ${x}px)`,
                  top: `calc(50% + ${y}px)`,
                  transform: 'translate(-50%, -50%)',
                }}
                initial={reduce ? undefined : { opacity: 0, scale: 0.8 }}
                animate={reduce ? undefined : { opacity: 1, scale: 1 }}
                transition={{ delay: 0.8 + index * 0.3, duration: 0.6 }}
              >
                <motion.span
                  className="relative flex h-16 w-16 items-center justify-center rounded-full"
                  style={{
                    background: `radial-gradient(circle, ${step.color}20, transparent 70%)`,
                    border: `2px solid ${step.color}60`,
                  }}
                  whileHover={reduce ? undefined : { scale: 1.1, boxShadow: `0 0 24px ${step.color}50` }}
                  transition={{ type: 'spring', stiffness: 400, damping: 25 }}
                >
                  <Icon className="h-6 w-6" style={{ color: step.color }} />
                </motion.span>

                <div className="flex flex-col">
                  <span className="text-xs font-extrabold text-[var(--color-night-100)]">
                    {step.title}
                  </span>
                  <span className="max-w-[140px] text-[10px] leading-4 text-[var(--color-night-200)]/50">
                    {step.desc}
                  </span>
                </div>
              </motion.div>
            );
          })}

          {/* center label */}
          <motion.span
            className="absolute text-[10px] font-bold tracking-widest text-[var(--color-night-200)]/40"
            initial={reduce ? undefined : { opacity: 0 }}
            animate={reduce ? undefined : { opacity: 1 }}
            transition={{ delay: 1.6 }}
          >
            {lang === 'fa' ? 'چرخه MRV' : 'MRV CYCLE'}
          </motion.span>
        </div>
      </Reveal>
    </section>
  );
}
