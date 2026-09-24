'use client';

import { useFormContext, useWatch } from 'react-hook-form';
import { useTranslations } from 'next-intl';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { z } from 'zod';

const step2Schema = z.object({
  description: z.string().optional(),
  address: z.string().optional(),
  latitude: z.number().optional(),
  longitude: z.number().optional(),
  website: z.string().url().optional(),
  socialLinks: z.string().optional(),
});

type Step2Input = z.infer<typeof step2Schema>;

export default function StoreStep2Form({ locale }: { locale: string }) {
  const t = useTranslations('market.storeWizard.step2');
  const { register, watch } = useFormContext<Step2Input>();

  const description = watch('description');

  return (
    <div className="space-y-4" dir={locale === 'fa' || locale === 'ar' ? 'rtl' : 'ltr'}>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <Textarea
            label={t('description')}
            placeholder={t('descriptionPlaceholder')}
            rows={4}
            {...register('description')}
          />
        </div>
        <div>
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
        <div className="sm:col-span-2">
          <Input
            label={t('website')}
            type="url"
            placeholder={t('websitePlaceholder')}
            {...register('website')}
          />
        </div>
        <div className="sm:col-span-2">
          <Input
            label={t('socialLinks')}
            placeholder={t('socialLinksPlaceholder')}
            {...register('socialLinks')}
          />
        </div>
      </div>

      {description && (
        <div className="mt-4 p-3 bg-primary/5 border border-primary/20 rounded text-sm text-primary">
          <strong>{t('preview')}: </strong>
          {description.substring(0, 100)}...
        </div>
      )}
    </div>
  );
}