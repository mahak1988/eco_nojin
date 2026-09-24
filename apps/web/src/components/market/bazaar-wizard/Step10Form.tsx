'use client';

import { useFormContext } from 'react-hook-form';
import { useTranslations } from 'next-intl';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { type Step10Input } from '@/lib/validation/bazaar-establishment';

export function Step10Form({ locale }: { locale: string }) {
  const t = useTranslations('market.bazaarWizard.step10');
  const { register, watch } = useFormContext<Step10Input>();

  const oversightSchedule = watch('oversightSchedule');
  const reviewCycleMonths = watch('reviewCycleMonths');

  return (
    <div className="space-y-4" dir={locale === 'fa' || locale === 'ar' ? 'rtl' : 'ltr'}>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <Textarea
            label={t('oversightSchedule')}
            placeholder={t('oversightSchedulePlaceholder')}
            rows={3}
            {...register('oversightSchedule')}
          />
        </div>
        <div>
          <Input
            label={t('supportContact')}
            placeholder={t('supportContactPlaceholder')}
            {...register('supportContact')}
          />
        </div>
        <div>
          <Input
            label={t('reviewCycleMonths')}
            type="number"
            min="1"
            placeholder={t('reviewCycleMonthsPlaceholder')}
            {...register('reviewCycleMonths', { valueAsNumber: true })}
          />
        </div>
      </div>

{(oversightSchedule || reviewCycleMonths) && (
        <div className="mt-4 p-3 bg-primary/5 border border-primary/20 rounded text-sm text-primary">
          <strong>{t('preview')}: </strong>
          {t('oversightPreview', { schedule: oversightSchedule ?? '', cycle: reviewCycleMonths ?? 0 })}
        </div>
      )}
    </div>
  );
}