'use client';

import { useTranslations } from 'next-intl';
import { FivePart } from '@/components/FivePart';

export default function LimitsPage() {
  const t = useTranslations('ai.limits');

  return (
    <main id="main">
      <div className="mx-auto max-w-4xl px-6 py-10">
        <FivePart
          title={t('title')}
          lead={t('lead')}
          what={t('what')}
          audience={t('audience')}
          evidence={[
            t('evidence1'),
            t('evidence2'),
            t('evidence3'),
          ]}
          limits={[
            t('limit1'),
            t('limit2'),
            t('limit3'),
            t('limit4'),
            t('limit5'),
          ]}
          next={[
            t('next1'),
            t('next2'),
          ]}
          limitsLabel={t('limitsTitle')}
          nextLabel={t('nextTitle')}
        />
      </div>
    </main>
  );
}