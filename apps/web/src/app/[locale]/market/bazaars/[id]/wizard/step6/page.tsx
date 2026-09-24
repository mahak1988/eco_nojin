'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Step6Form } from '@/components/market/bazaar-wizard/Step6Form';
import { type Step6Input, step6Schema } from '@/lib/validation/bazaar-establishment';

export default function Step6Page() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';
  const t = useTranslations('market.bazaarWizard.step6');

  return (
    <FormProvider {...useForm<Step6Input>({ resolver: zodResolver(step6Schema), mode: 'onChange' })}>
      <Step6Form locale={locale} />
    </FormProvider>
  );
}