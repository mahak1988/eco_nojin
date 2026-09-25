'use client';

import { useTranslations } from 'next-intl';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';

export const BAZAAR_MARKETPLACES_SOURCE = '/api/v1/marketplace/marketplaces';
export const WIZARD_TOTAL_STEPS = 10;
const WIZARD_STEP_NUMBERS = Array.from({ length: WIZARD_TOTAL_STEPS }, (_, index) => index + 1);

export interface BazaarEstablishmentWizardProps {
  locale: string;
  tenantId?: string;
  onComplete?: () => void;
}

/**
 * The 10-step bazaar establishment flow is intentionally not interactive.
 *
 * The gateway exposes `POST /api/v1/marketplace/marketplaces` for the identity
 * step only; the geographic boundary, founding board, rules, vendors, 5-party
 * signatures, verification, registration, launch and oversight steps have no
 * endpoint. The component therefore reports an explicit unavailable state
 * instead of collecting input it cannot persist, and it never posts a request
 * or reports a success. `onComplete` is not invoked while the flow is offline.
 */
export function BazaarEstablishmentWizard({ locale }: BazaarEstablishmentWizardProps) {
  const t = useTranslations('market.template');
  const statusLine = useTranslations('statusLine');

  return (
    <div
      className="bazaar-wizard space-y-4"
      data-locale={locale}
      dir={locale === 'fa' || locale === 'ar' ? 'rtl' : 'ltr'}
    >
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="flex-1 text-xl font-bold text-ink">{t('title')}</h2>
        <ProvenanceStamp source={BAZAAR_MARKETPLACES_SOURCE} label={t('source')} />
      </div>

      <Card density="cozy">
        <StatusDot state="warn" label={t('status')} />
        <p className="mt-3 text-sm text-ink-soft">{t('unavailableDescription')}</p>
        <p role="status" className="mt-2 text-sm text-ink-soft">
          {statusLine('unavailable')}
        </p>
        <ol
          className="mt-4 flex flex-wrap gap-2 text-xs text-ink-soft"
          aria-label={t('contractTitle')}
        >
          {WIZARD_STEP_NUMBERS.map((step) => (
            <li key={`wizard-step-${step}`} className="num">
              {step}
            </li>
          ))}
        </ol>
      </Card>
    </div>
  );
}
