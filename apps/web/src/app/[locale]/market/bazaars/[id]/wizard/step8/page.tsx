'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useParams } from 'next/navigation';
import { FormProvider, useForm } from 'react-hook-form';
import { Step8Form } from '@/components/market/bazaar-wizard/Step8Form';
import { type Step8Input, step8Schema } from '@/lib/validation/bazaar-establishment';

export default function Step8Page() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';

  return (
    <FormProvider
      {...useForm<Step8Input>({ resolver: zodResolver(step8Schema), mode: 'onChange' })}
    >
      <Step8Form locale={locale} />
    </FormProvider>
  );
}
