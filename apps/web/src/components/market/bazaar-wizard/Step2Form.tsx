'use client';

import { useFormContext, useWatch } from 'react-hook-form';
import { useTranslations } from 'next-intl';
import { Input } from '@/components/ui/Input';
import { type Step2Input } from '@/lib/validation/bazaar-establishment';

export function Step2Form({ locale }: { locale: string }) {
  const t = useTranslations('market.bazaarWizard.step2');
  const { register, watch } = useFormContext<Step2Input>();

  const areaHa = watch('areaHa');

  return (
    <div className="space-y-4" dir={locale === 'fa' || locale === 'ar' ? 'rtl' : 'ltr'}>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <Input
            label={t('areaHa')}
            type="number"
            step="0.01"
            min="0"
            placeholder={t('areaHaPlaceholder')}
            {...register('areaHa', { valueAsNumber: true })}
          />
        </div>
        <div>
          <Input
            label={t('boundingBox')}
            placeholder={t('boundingBoxPlaceholder')}
            {...register('boundingBox')}
          />
        </div>
        <div className="sm:col-span-2">
          <Input
            label={t('polygonGeojson')}
            placeholder={t('polygonGeojsonPlaceholder')}
            {...register('polygonGeojson')}
          />
        </div>
      </div>

      {areaHa && (
        <div className="mt-4 p-3 bg-primary/5 border border-primary/20 rounded text-sm text-primary">
          <strong>{t('preview')}: </strong>
          {t('areaPreview', { area: areaHa })}
        </div>
      )}
    </div>
  );
}