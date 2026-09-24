'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Step3Form } from '@/components/market/bazaar-wizard/Step3Form';
import { type Step3Input, step3Schema } from '@/lib/validation/bazaar-establishment';

export default function Step3Page() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';
  const t = useTranslations('market.bazaarWizard.step3');

  return (
    <FormProvider {...useForm<Step3Input>({ resolver: zodResolver(step3Schema), mode: 'onChange' })}>
      <Step3Form locale={locale} />
    </FormProvider>
  );
}