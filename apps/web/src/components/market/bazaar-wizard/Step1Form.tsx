'use client';

import { useFormContext, useWatch } from 'react-hook-form';
import { useTranslations } from 'next-intl';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Textarea } from '@/components/ui/Textarea';
import { type Step1Input } from '@/lib/validation/bazaar-establishment';

export function Step1Form({ locale }: { locale: string }) {
  const t = useTranslations('market.bazaarWizard.step1');
  const { register, setValue, watch } = useFormContext<Step1Input>();

  const name = watch('name');
  const code = watch('code');
  const bazaarType = watch('bazaarType');
  const description = watch('description');
  const address = watch('address');
  const latitude = watch('latitude');
  const longitude = watch('longitude');

  return (
    <div className="space-y-4" dir={locale === 'fa' || locale === 'ar' ? 'rtl' : 'ltr'}>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <Input
            label={t('name')}
            placeholder={t('namePlaceholder')}
            {...register('name')}
          />
        </div>
        <div>
          <Input
            label={t('code')}
            placeholder={t('codePlaceholder')}
            {...register('code')}
          />
        </div>
        <div>
          <Select
            label={t('bazaarType')}
            {...register('bazaarType')}
          >
            <option value="rural">{t('bazaarType.rural')}</option>
            <option value="inter_village">{t('bazaarType.interVillage')}</option>
            <option value="regional">{t('bazaarType.regional')}</option>
            <option value="specialty">{t('bazaarType.specialty')}</option>
          </Select>
        </div>
        <div className="sm:col-span-2">
          <Textarea
            label={t('description')}
            placeholder={t('descriptionPlaceholder')}
            rows={3}
            {...register('description')}
          />
        </div>
        <div className="sm:col-span-2">
          <Input
            label={t('address')}
            placeholder={t('addressPlaceholder')}
            {...register('address')}
          />
        </div>
        <div>
          <Input
            label={t('latitude')}
            type="number"
            step="0.000001"
            min="-90"
            max="90"
            placeholder={t('latitudePlaceholder')}
            {...register('latitude', { valueAsNumber: true })}
          />
        </div>
        <div>
          <Input
            label={t('longitude')}
            type="number"
            step="0.000001"
            min="-180"
            max="180"
            placeholder={t('longitudePlaceholder')}
            {...register('longitude', { valueAsNumber: true })}
          />
        </div>
      </div>

      {(name || code) && (
        <div className="mt-4 p-3 bg-primary/5 border border-primary/20 rounded text-sm text-primary">
          <strong>{t('preview')}: </strong>
          {name} ({code}) — {t(`bazaarType.${bazaarType}`)}
        </div>
      )}
    </div>
  );
}