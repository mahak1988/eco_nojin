'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Step10Form } from '@/components/market/bazaar-wizard/Step10Form';
import { type Step10Input, step10Schema } from '@/lib/validation/bazaar-establishment';

export default function Step10Page() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';
  const t = useTranslations('market.bazaarWizard.step10');

  return (
    <FormProvider {...useForm<Step10Input>({ resolver: zodResolver(step10Schema), mode: 'onChange' })}>
      <Step10Form locale={locale} />
    </FormProvider>
  );
}