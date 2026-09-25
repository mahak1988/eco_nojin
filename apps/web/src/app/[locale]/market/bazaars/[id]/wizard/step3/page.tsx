'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useParams } from 'next/navigation';
import { FormProvider, useForm } from 'react-hook-form';
import { Step3Form } from '@/components/market/bazaar-wizard/Step3Form';
import { type Step3Input, step3Schema } from '@/lib/validation/bazaar-establishment';

export default function Step3Page() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';

  return (
    <FormProvider
      {...useForm<Step3Input>({ resolver: zodResolver(step3Schema), mode: 'onChange' })}
    >
      <Step3Form locale={locale} />
    </FormProvider>
  );
}
