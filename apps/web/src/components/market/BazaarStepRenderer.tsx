'use client';

import { useTranslations } from 'next-intl';
import {
  BAZAAR_MARKETPLACES_SOURCE,
  WIZARD_TOTAL_STEPS,
} from '@/components/BazaarEstablishmentWizard';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';

interface BazaarStepRendererProps {
  step: number;
  locale: string;
}

/**
 * Individual establishment steps stay unavailable for the same reason as the
 * wizard shell: no gateway endpoint exists for them, so the step renders its
 * real state instead of an untranslated placeholder form.
 */
export function BazaarStepRenderer({ step, locale }: BazaarStepRendererProps) {
  const t = useTranslations('market.template');
  const statusLine = useTranslations('statusLine');
  const safeStep = Math.min(Math.max(step, 1), WIZARD_TOTAL_STEPS);

  return (
    <fieldset
      className="space-y-4"
      dir={locale === 'fa' || locale === 'ar' ? 'rtl' : 'ltr'}
      aria-labelledby={`step-${safeStep}-legend`}
    >
      <legend id={`step-${safeStep}-legend`} className="text-lg font-semibold text-ink">
        <span className="num mr-2 text-sm text-ink-faint">{safeStep}</span>
        {t('title')}
      </legend>
      <Card density="cozy">
        <div className="flex flex-wrap items-center gap-3">
          <StatusDot state="warn" label={t('status')} />
          <ProvenanceStamp source={BAZAAR_MARKETPLACES_SOURCE} label={t('source')} />
        </div>
        <p className="mt-3 text-sm text-ink-soft">{t('unavailableDescription')}</p>
        <p role="status" className="mt-2 text-sm text-ink-soft">
          {statusLine('unavailable')}
        </p>
      </Card>
    </fieldset>
  );
}
