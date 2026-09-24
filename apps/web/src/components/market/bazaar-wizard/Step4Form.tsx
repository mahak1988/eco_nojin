'use client';

import { useFormContext, useWatch } from 'react-hook-form';
import { useTranslations } from 'next-intl';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { type Step4Input } from '@/lib/validation/bazaar-establishment';

export function Step4Form({ locale }: { locale: string }) {
  const t = useTranslations('market.bazaarWizard.step4');
  const { register, watch } = useFormContext<Step4Input>();

  const storeCount = watch('storeCount');

  return (
    <div className="space-y-4" dir={locale === 'fa' || locale === 'ar' ? 'rtl' : 'ltr'}>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <Input
            label={t('storeCount')}
            type="number"
            min="0"
            placeholder={t('storeCountPlaceholder')}
            {...register('storeCount', { valueAsNumber: true })}
          />
        </div>
        <div className="sm:col-span-2">
          <Textarea
            label={t('rulesDocument')}
            placeholder={t('rulesDocumentPlaceholder')}
            rows={4}
            {...register('rulesDocument')}
          />
        </div>
        <div className="sm:col-span-2">
          <Textarea
            label={t('operatingHours')}
            placeholder={t('operatingHoursPlaceholder')}
            rows={3}
            {...register('operatingHours')}
          />
        </div>
        <div className="sm:col-span-2">
          <Textarea
            label={t('membershipRules')}
            placeholder={t('membershipRulesPlaceholder')}
            rows={4}
            {...register('membershipRules')}
          />
        </div>
      </div>

      {storeCount !== undefined && storeCount > 0 && (
        <div className="mt-4 p-3 bg-primary/5 border border-primary/20 rounded text-sm text-primary">
          <strong>{t('preview')}: </strong>
          {t('storeCountPreview', { count: storeCount })}
        </div>
      )}
    </div>
  );
}