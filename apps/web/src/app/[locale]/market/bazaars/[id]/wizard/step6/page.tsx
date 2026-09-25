'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useParams } from 'next/navigation';
import { FormProvider, useForm } from 'react-hook-form';
import { Step6Form } from '@/components/market/bazaar-wizard/Step6Form';
import { type Step6Input, step6Schema } from '@/lib/validation/bazaar-establishment';

export default function Step6Page() {
  const params = useParams();
  const locale = (params.locale as string) ?? 'fa';

  return (
    <FormProvider
      {...useForm<Step6Input>({ resolver: zodResolver(step6Schema), mode: 'onChange' })}
    >
      <Step6Form locale={locale} />
    </FormProvider>
  );
}
