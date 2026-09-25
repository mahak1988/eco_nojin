'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useParams } from 'next/navigation';
import { FormProvider, useForm } from 'react-hook-form';
import { Step10Form } from '@/components/market/bazaar-wizard/Step10Form';
import { type Step10Input, step10Schema } from '@/lib/validation/bazaar-establishment';

export default function Step10Page() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';

  return (
    <FormProvider
      {...useForm<Step10Input>({ resolver: zodResolver(step10Schema), mode: 'onChange' })}
    >
      <Step10Form locale={locale} />
    </FormProvider>
  );
}
