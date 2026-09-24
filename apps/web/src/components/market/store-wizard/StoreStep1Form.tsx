'use client';

import { useSearchParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useFormContext } from 'react-hook-form';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { z } from 'zod';

const step1Schema = z.object({
  bazaarId: z.string().optional(),
  storeName: z.string().min(2),
  storeCode: z.string().min(3),
  storeType: z.enum(['producer', 'reseller', 'cooperative', 'artisan']),
  ownerName: z.string().optional(),
  contactPhone: z.string().optional(),
  contactEmail: z.string().email().optional(),
});

type Step1Input = z.infer<typeof step1Schema>;

export default function StoreStep1Form({ locale }: { locale: string }) {
  const t = useTranslations('market.storeWizard.step1');
  const searchParams = useSearchParams();
  const { register, setValue, watch } = useFormContext<Step1Input>();

  const bazaarId = searchParams.get('bazaar') || '';

  return (
    <div className="space-y-4" dir={locale === 'fa' || locale === 'ar' ? 'rtl' : 'ltr'}>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <Input
            label={t('bazaarSelection')}
            placeholder={t('bazaarSelectionPlaceholder')}
            disabled
            defaultValue={bazaarId}
            {...register('bazaarId')}
          />
        </div>
        <div>
          <Input
            label={t('storeName')}
            placeholder={t('storeNamePlaceholder')}
            {...register('storeName')}
          />
        </div>
        <div>
          <Input
            label={t('storeCode')}
            placeholder={t('storeCodePlaceholder')}
            {...register('storeCode')}
          />
        </div>
        <div>
          <Select
            label={t('storeType')}
            {...register('storeType')}
          >
            <option value="producer">{t('storeType.producer')}</option>
            <option value="reseller">{t('storeType.reseller')}</option>
            <option value="cooperative">{t('storeType.cooperative')}</option>
            <option value="artisan">{t('storeType.artisan')}</option>
          </Select>
        </div>
        <div className="sm:col-span-2">
          <Input
            label={t('ownerName')}
            placeholder={t('ownerNamePlaceholder')}
            {...register('ownerName')}
          />
        </div>
        <div>
          <Input
            label={t('contactPhone')}
            type="tel"
            placeholder={t('contactPhonePlaceholder')}
            {...register('contactPhone')}
          />
        </div>
        <div>
          <Input
            label={t('contactEmail')}
            type="email"
            placeholder={t('contactEmailPlaceholder')}
            {...register('contactEmail')}
          />
        </div>
      </div>

      {bazaarId && (
        <div className="mt-4 p-3 bg-primary/5 border border-primary/20 rounded text-sm text-primary">
          <strong>{t('preview')}: </strong>
          {t('bazaarPreview', { id: bazaarId })}
        </div>
      )}
    </div>
  );
}