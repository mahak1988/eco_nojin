'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Step5Form } from '@/components/market/bazaar-wizard/Step5Form';
import { type Step5Input, step5Schema } from '@/lib/validation/bazaar-establishment';

export default function Step5Page() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';
  const t = useTranslations('market.bazaarWizard.step5');

  return (
    <FormProvider {...useForm<Step5Input>({ resolver: zodResolver(step5Schema), mode: 'onChange' })}>
      <Step5Form locale={locale} />
    </FormProvider>
  );
}