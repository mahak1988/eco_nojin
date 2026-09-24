'use client';

import { useFormContext, useWatch } from 'react-hook-form';
import { useTranslations } from 'next-intl';
import { Input } from '@/components/ui/Input';
import { type Step8Input } from '@/lib/validation/bazaar-establishment';

export function Step8Form({ locale }: { locale: string }) {
  const t = useTranslations('market.bazaarWizard.step8');
  const { register, watch } = useFormContext<Step8Input>();

  const registrationNumber = watch('registrationNumber');
  const registrationDate = watch('registrationDate');

  return (
    <div className="space-y-4" dir={locale === 'fa' || locale === 'ar' ? 'rtl' : 'ltr'}>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <Input
            label={t('registrationNumber')}
            placeholder={t('registrationNumberPlaceholder')}
            {...register('registrationNumber')}
          />
        </div>
        <div>
          <Input
            label={t('registrationDate')}
            type="date"
            {...register('registrationDate')}
          />
        </div>
        <div>
          <Input
            label={t('regulatorId')}
            placeholder={t('regulatorIdPlaceholder')}
            {...register('regulatorId')}
          />
        </div>
        <div>
          <Input
            label={t('systemId')}
            placeholder={t('systemIdPlaceholder')}
            {...register('systemId')}
          />
        </div>
      </div>

      {(registrationNumber || registrationDate) && (
        <div className="mt-4 p-3 bg-primary/5 border border-primary/20 rounded text-sm text-primary">
          <strong>{t('preview')}: </strong>
          {t('registrationPreview', { number: String(registrationNumber ?? ''), date: String(registrationDate ?? '') })}
        </div>
      )}
    </div>
  );
}