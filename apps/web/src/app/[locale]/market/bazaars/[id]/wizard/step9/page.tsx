'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useParams } from 'next/navigation';
import { FormProvider, useForm } from 'react-hook-form';
import Step9Form from '@/components/market/bazaar-wizard/Step9Form';
import { type Step9Input, step9Schema } from '@/lib/validation/bazaar-establishment';

export default function Step9Page() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';

  return (
    <FormProvider
      {...useForm<Step9Input>({ resolver: zodResolver(step9Schema), mode: 'onChange' })}
    >
      <Step9Form locale={locale} />
    </FormProvider>
  );
}
