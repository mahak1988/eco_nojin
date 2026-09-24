'use client';

import { useTranslations } from 'next-intl';
import { Card } from '@/components/ui/Card';
import { WIZARD_TOTAL_STEPS, stepLabels } from '@/components/BazaarEstablishmentWizard';

interface BazaarStepRendererProps {
  step: number;
  locale: string;
  watchedStep1: { name?: string } | undefined;
}

export function BazaarStepRenderer({ step, locale, watchedStep1 }: BazaarStepRendererProps) {
  const stepTitle = stepLabels[step - 1];
  const t = useTranslations('market.bazaarWizard');

  return (
    <fieldset className="space-y-4" aria-labelledby={`step-${step}-legend`}>
      <legend id={`step-${step}-legend`} className="text-lg font-semibold text-ink">
        <span className="num text-sm text-ink-faint mr-2">{step}</span>
        {locale === 'fa' ? stepTitle.fa : stepTitle.en}
      </legend>
      <div className="card p-5 min-h-[120px]">
        <p className="text-sm text-ink-soft">
          {locale === 'fa'
            ? `این قسمت مرحلهٔ ${step} — «${stepTitle.fa}» — اسکافلد است. پیاده‌سازی کامل در فاز ۳ تحویل داده می‌شود.`
            : `Step ${step}: "${stepTitle.en}" — scaffold. Full implementation delivered in Phase 3.`}
        </p>
        {step === 1 && watchedStep1 && (
          <div className="mt-3 text-xs text-ink-faint">
            {locale === 'fa'
              ? `پیش‌نمایش: ${watchedStep1.name || '...'}`
              : `Preview: ${watchedStep1.name || '...'}`}
          </div>
        )}
      </div>
    </fieldset>
  );
}