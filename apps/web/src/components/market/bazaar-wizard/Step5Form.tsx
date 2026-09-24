'use client';

import { useFormContext, useFieldArray } from 'react-hook-form';
import { useTranslations } from 'next-intl';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

const VENDOR_CATEGORIES = [
  'agriculture', 'handicrafts', 'food_processing', 'textiles',
  'dairy', 'meat', 'bakery', 'spices', 'herbal', 'other'
];

export function Step5Form({ locale }: { locale: string }) {
  const t = useTranslations('market.bazaarWizard.step5');
  const { register, control, watch } = useFormContext();
  const { fields, append, remove } = useFieldArray({ control, name: 'vendorIds' });
  const { fields: catFields, append: appendCat, remove: removeCat } = useFieldArray({ control, name: 'vendorCategories' });
  const vendorIds = watch('vendorIds') ?? [];
  const expectedStoreCount = watch('expectedStoreCount') ?? 0;
  const vendorCategories = watch('vendorCategories') ?? [];

  return (
    <div className="space-y-4" dir={locale === 'fa' || locale === 'ar' ? 'rtl' : 'ltr'}>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <Input
            label={t('expectedStoreCount')}
            type="number"
            min="0"
            placeholder={t('expectedStoreCountPlaceholder')}
            {...register('expectedStoreCount', { valueAsNumber: true })}
          />
        </div>
      </div>

      <div className="mt-6">
        <h4 className="font-medium text-ink mb-3">{t('vendorIds')}</h4>
        <div className="grid gap-3">
          {fields.map((field, index) => (
            <div key={field.id} className="flex gap-2">
              <Input
                placeholder={t('vendorIdPlaceholder')}
                {...register(`vendorIds.${index}`)}
                className="flex-1"
              />
              {fields.length > 1 && (
                <Button variant="ghost" size="sm" onClick={() => remove(index)}>
                  {t('remove')}
                </Button>
              )}
            </div>
          ))}
          <Button variant="ghost" size="sm" onClick={() => append('')}>
            + {t('addVendorId')}
          </Button>
        </div>
      </div>

      <div className="mt-6">
        <h4 className="font-medium text-ink mb-3">{t('vendorCategories')}</h4>
        <div className="flex flex-wrap gap-2">
          {VENDOR_CATEGORIES.map(cat => (
            <label key={cat} className="inline-flex items-center gap-2 px-3 py-1.5 rounded border text-sm cursor-pointer hover:bg-surface-alt">
              <input
                type="checkbox"
                checked={vendorCategories.includes(cat)}
                onChange={e => {
                  if (e.target.checked) {
                    appendCat(cat);
                  } else {
                    const idx = (vendorCategories as string[]).indexOf(cat);
                    if (idx >= 0) removeCat(idx);
                  }
                }}
              />
              {t(`vendorCategory.${cat}`)}
            </label>
          ))}
        </div>
      </div>

      {(vendorIds.length > 0 || expectedStoreCount) && (
        <div className="mt-4 p-3 bg-primary/5 border border-primary/20 rounded text-sm text-primary">
          <strong>{t('preview')}: </strong>
          {vendorIds.length} {t('vendorIds')}, {expectedStoreCount || 0} {t('expectedStores')}, {vendorCategories.length} {t('categories')}
        </div>
      )}
    </div>
  );
}