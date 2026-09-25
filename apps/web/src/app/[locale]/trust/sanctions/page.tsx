'use client';

import { useTranslations } from 'next-intl';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';

export default function SanctionsPage() {
  const t = useTranslations('market.template');
  const trust = useTranslations('trust');
  const status = useTranslations('statusLine');

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{trust('title')}</h1>
        <div className="mt-6 flex flex-wrap items-center gap-4">
          <StatusDot state="down" label={status('unavailable')} />
          <ProvenanceStamp
            source={t('source')}
            label={t('source')}
            verified={false}
            method={t('method')}
          />
        </div>
        <Card density="cozy" className="mt-6">
          <h2 className="font-semibold text-ink">{t('unavailableTitle')}</h2>
          <p className="mt-2 text-sm text-ink-soft">{t('unavailableDescription')}</p>
        </Card>
        <div className="mt-6 grid gap-3 md:grid-cols-2">
          <div className="rounded-md border border-line p-4">
            <h3 className="font-medium text-ink">{t('contractTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{t('contractDescription')}</p>
          </div>
          <div className="rounded-md border border-line p-4">
            <h3 className="font-medium text-ink">{t('nextTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{t('nextDescription')}</p>
          </div>
        </div>
      </div>
    </main>
  );
}
