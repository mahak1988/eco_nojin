import { useState, useEffect } from 'react';
import { useLang } from '../../i18n/LanguageContext';
import { SkipForward, SkipBack, X } from 'lucide-react';

/** Onboarding tour walkthrough. */
export default function TourGuide() {
  const { lang } = useLang();
  const [active, setActive] = useState(false);
  const [step, setStep] = useState(0);

  const steps = [
    { title: 'خانه', text: 'به صفحه اصلی خوش آمدید' },
    { title: 'پلتفرم', text: 'مدل‌ها و کانال‌های دسترسی' },
    { title: 'تأثیر', text: 'آمار و شاخص‌های بلادرنگ' },
    { title: 'پروژه‌ها', text: 'نقشه و مشاهده پروژه‌ها' },
  ];

  useEffect(() => {
    const timer = setTimeout(() => setActive(true), 5000);
    return () => clearTimeout(timer);
  }, []);

  if (!active) return (
    <button
      type="button"
      onClick={() => setActive(true)}
      className="fixed bottom-6 left-6 z-50 rounded-full bg-[var(--color-leaf-500)] px-4 py-2 text-xs font-extrabold text-[var(--color-night-950)] shadow-lg hover:scale-105 transition-transform"
    >
      {lang === 'fa' ? '🚀 راهنما' : '🚀 Tour'}
    </button>
  );

  const currentStep = steps[step];

  return (
    <div className="fixed bottom-6 left-6 z-50 max-w-xs">
      <div className="rounded-2xl glass p-4 border border-[var(--color-leaf-500)]/20">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-bold text-[var(--color-leaf-300)]">
            {step + 1}/{steps.length}
          </span>
          <button type="button" onClick={() => setActive(false)}>
            <X className="h-3 w-3 text-[var(--color-night-200)]/40" aria-hidden />
          </button>
        </div>
        <h4 className="text-sm font-bold text-[var(--color-night-100)] mb-1">{currentStep.title}</h4>
        <p className="text-xs text-[var(--color-night-200)]/60 mb-3">{currentStep.text}</p>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            disabled={step === 0}
            className="glass px-3 py-1.5 rounded-lg text-xs disabled:opacity-30"
          >
            <SkipBack className="h-3 w-3 inline" aria-hidden />
          </button>
          <button
            type="button"
            onClick={() => step < steps.length - 1 ? setStep((s) => s + 1) : setActive(false)}
            className="bg-[var(--color-leaf-500)] px-3 py-1.5 rounded-lg text-xs font-bold text-[var(--color-night-950)]"
          >
            {step < steps.length - 1 ? (
              <SkipForward className="h-3 w-3 inline" aria-hidden />
            ) : (
              'تمام'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
