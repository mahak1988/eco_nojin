'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import Step9Form from '@/components/market/bazaar-wizard/Step9Form';
import { type Step9Input, step9Schema } from '@/lib/validation/bazaar-establishment';

export default function Step9Page() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';
  const t = useTranslations('market.bazaarWizard.step9');

  return (
    <FormProvider {...useForm<Step9Input>({ resolver: zodResolver(step9Schema), mode: 'onChange' })}>
      <Step9Form locale={locale} />
    </FormProvider>
  );
}