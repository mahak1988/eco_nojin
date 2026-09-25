'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useParams } from 'next/navigation';
import { FormProvider, useForm } from 'react-hook-form';
import { Step4Form } from '@/components/market/bazaar-wizard/Step4Form';
import { type Step4Input, step4Schema } from '@/lib/validation/bazaar-establishment';

export default function Step4Page() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';

  return (
    <FormProvider
      {...useForm<Step4Input>({ resolver: zodResolver(step4Schema), mode: 'onChange' })}
    >
      <Step4Form locale={locale} />
    </FormProvider>
  );
}
