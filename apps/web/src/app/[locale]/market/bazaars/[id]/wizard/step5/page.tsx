'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useParams } from 'next/navigation';
import { FormProvider, useForm } from 'react-hook-form';
import { Step5Form } from '@/components/market/bazaar-wizard/Step5Form';
import { type Step5Input, step5Schema } from '@/lib/validation/bazaar-establishment';

export default function Step5Page() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';

  return (
    <FormProvider
      {...useForm<Step5Input>({ resolver: zodResolver(step5Schema), mode: 'onChange' })}
    >
      <Step5Form locale={locale} />
    </FormProvider>
  );
}
