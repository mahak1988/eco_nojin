'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Step4Form } from '@/components/market/bazaar-wizard/Step4Form';
import { type Step4Input, step4Schema } from '@/lib/validation/bazaar-establishment';

export default function Step4Page() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';
  const t = useTranslations('market.bazaarWizard.step4');

  return (
    <FormProvider {...useForm<Step4Input>({ resolver: zodResolver(step4Schema), mode: 'onChange' })}>
      <Step4Form locale={locale} />
    </FormProvider>
  );
}