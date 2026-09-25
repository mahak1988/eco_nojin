'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useParams } from 'next/navigation';
import { FormProvider, useForm } from 'react-hook-form';
import { Step7Form } from '@/components/market/bazaar-wizard/Step7Form';
import { type Step7Input, step7Schema } from '@/lib/validation/bazaar-establishment';

export default function Step7Page() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';

  return (
    <FormProvider
      {...useForm<Step7Input>({ resolver: zodResolver(step7Schema), mode: 'onChange' })}
    >
      <Step7Form locale={locale} />
    </FormProvider>
  );
}
