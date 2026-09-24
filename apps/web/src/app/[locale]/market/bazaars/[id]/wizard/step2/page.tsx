'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Step2Form } from '@/components/market/bazaar-wizard/Step2Form';
import { type Step2Input, step2Schema } from '@/lib/validation/bazaar-establishment';

export default function Step2Page() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';
  const t = useTranslations('market.bazaarWizard.step2');

  return (
    <FormProvider {...useForm<Step2Input>({ resolver: zodResolver(step2Schema), mode: 'onChange' })}>
      <Step2Form locale={locale} />
    </FormProvider>
  );
}