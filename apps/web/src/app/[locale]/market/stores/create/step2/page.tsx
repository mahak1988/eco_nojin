'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import StoreStep2Form from '@/components/market/store-wizard/StoreStep2Form';
import { z } from 'zod';

const step2Schema = z.object({
  description: z.string().optional(),
  address: z.string().optional(),
  latitude: z.number().optional(),
  longitude: z.number().optional(),
  website: z.string().url().optional(),
  socialLinks: z.string().optional(),
});

type Step2Input = z.infer<typeof step2Schema>;

export default function StoreStep2Page() {
  const params = useParams();
  const locale = params.locale as string;
  const t = useTranslations('market.storeWizard.step2');

  return (
    <FormProvider {...useForm<Step2Input>({ resolver: zodResolver(step2Schema), mode: 'onChange' })}>
      <StoreStep2Form locale={locale} />
    </FormProvider>
  );
}