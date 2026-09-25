'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useParams } from 'next/navigation';
import { FormProvider, useForm } from 'react-hook-form';
import { Step2Form } from '@/components/market/bazaar-wizard/Step2Form';
import { type Step2Input, step2Schema } from '@/lib/validation/bazaar-establishment';

export default function Step2Page() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';

  return (
    <FormProvider
      {...useForm<Step2Input>({ resolver: zodResolver(step2Schema), mode: 'onChange' })}
    >
      <Step2Form locale={locale} />
    </FormProvider>
  );
}
