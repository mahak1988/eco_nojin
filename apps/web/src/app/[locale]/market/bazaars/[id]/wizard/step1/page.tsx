'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Step1Form } from '@/components/market/bazaar-wizard/Step1Form';
import { type Step1Input, step1Schema } from '@/lib/validation/bazaar-establishment';

export default function Step1Page() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';
  const t = useTranslations('market.bazaarWizard.step1');

  return (
    <FormProvider {...useForm<Step1Input>({ resolver: zodResolver(step1Schema), mode: 'onChange' })}>
      <Step1Form locale={locale} />
    </FormProvider>
  );
}