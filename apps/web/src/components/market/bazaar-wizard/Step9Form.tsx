'use client';

import { useFormContext, useWatch } from 'react-hook-form';
import { useTranslations } from 'next-intl';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { type Step9Input } from '@/lib/validation/bazaar-establishment';

export default function Step9Form({ locale }: { locale: string }) {
  const t = useTranslations('market.bazaarWizard.step9');
  const { register, watch } = useFormContext<Step9Input>();

  const launchDate = watch('launchDate');
  const initialStockCount = watch('initialStockCount');

  return (
    <div className="space-y-4" dir={locale === 'fa' || locale === 'ar' ? 'rtl' : 'ltr'}>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <Input
            label={t('launchDate')}
            type="date"
            {...register('launchDate')}
          />
        </div>
        <div>
          <Input
            label={t('initialStockCount')}
            type="number"
            min="0"
            placeholder={t('initialStockCountPlaceholder')}
            {...register('initialStockCount', { valueAsNumber: true })}
          />
        </div>
        <div className="sm:col-span-2">
          <Textarea
            label={t('operationalNotes')}
            placeholder={t('operationalNotesPlaceholder')}
            rows={4}
            {...register('operationalNotes')}
          />
        </div>
      </div>

      {(launchDate || initialStockCount !== undefined) && (
        <div className="mt-4 p-3 bg-primary/5 border border-primary/20 rounded text-sm text-primary">
          <strong>{t('preview')}: </strong>
          {t('launchPreview', { date: launchDate ?? '', stock: initialStockCount ?? 0 })}
        </div>
      )}
    </div>
  );
}