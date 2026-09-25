'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useParams } from 'next/navigation';
import { FormProvider, useForm } from 'react-hook-form';
import { Step1Form } from '@/components/market/bazaar-wizard/Step1Form';
import { type Step1Input, step1Schema } from '@/lib/validation/bazaar-establishment';

export default function Step1Page() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';

  return (
    <FormProvider
      {...useForm<Step1Input>({ resolver: zodResolver(step1Schema), mode: 'onChange' })}
    >
      <Step1Form locale={locale} />
    </FormProvider>
  );
}
