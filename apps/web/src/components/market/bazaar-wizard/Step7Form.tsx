'use client';

import { useFormContext, useWatch } from 'react-hook-form';
import { useTranslations } from 'next-intl';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { type Step7Input } from '@/lib/validation/bazaar-establishment';

export function Step7Form({ locale }: { locale: string }) {
  const t = useTranslations('market.bazaarWizard.step7');
  const { register, watch } = useFormContext<Step7Input>();

  const verifiedBy = watch('verifiedBy');
  const verificationDate = watch('verificationDate');

  return (
    <div className="space-y-4" dir={locale === 'fa' || locale === 'ar' ? 'rtl' : 'ltr'}>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <Input
            label={t('verifiedBy')}
            placeholder={t('verifiedByPlaceholder')}
            {...register('verifiedBy')}
          />
        </div>
        <div>
          <Input
            label={t('verificationDate')}
            type="date"
            {...register('verificationDate')}
          />
        </div>
        <div className="sm:col-span-2">
          <Textarea
            label={t('verificationNotes')}
            placeholder={t('verificationNotesPlaceholder')}
            rows={4}
            {...register('verificationNotes')}
          />
        </div>
      </div>

{(verifiedBy || verificationDate) && (
        <div className="mt-4 p-3 bg-primary/5 border border-primary/20 rounded text-sm text-primary">
          <strong>{t('preview')}: </strong>
          {t('verificationPreview', { by: verifiedBy ?? '', date: verificationDate ?? '' })}
        </div>
      )}
    </div>
  );
}