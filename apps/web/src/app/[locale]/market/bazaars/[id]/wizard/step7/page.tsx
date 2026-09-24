'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Step7Form } from '@/components/market/bazaar-wizard/Step7Form';
import { type Step7Input, step7Schema } from '@/lib/validation/bazaar-establishment';

export default function Step7Page() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';
  const t = useTranslations('market.bazaarWizard.step7');

  return (
    <FormProvider {...useForm<Step7Input>({ resolver: zodResolver(step7Schema), mode: 'onChange' })}>
      <Step7Form locale={locale} />
    </FormProvider>
  );
}