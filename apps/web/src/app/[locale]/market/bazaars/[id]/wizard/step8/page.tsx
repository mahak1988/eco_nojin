'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Step8Form } from '@/components/market/bazaar-wizard/Step8Form';
import { type Step8Input, step8Schema } from '@/lib/validation/bazaar-establishment';

export default function Step8Page() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';
  const t = useTranslations('market.bazaarWizard.step8');

  return (
    <FormProvider {...useForm<Step8Input>({ resolver: zodResolver(step8Schema), mode: 'onChange' })}>
      <Step8Form locale={locale} />
    </FormProvider>
  );
}