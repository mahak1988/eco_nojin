'use client';

import { useParams, useSearchParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import StoreStep1Form from '@/components/market/store-wizard/StoreStep1Form';
import { z } from 'zod';

const step1Schema = z.object({
  bazaarId: z.string().optional(),
  storeName: z.string().min(2),
  storeCode: z.string().min(3),
  storeType: z.enum(['producer', 'reseller', 'cooperative', 'artisan']),
  ownerName: z.string().optional(),
  contactPhone: z.string().optional(),
  contactEmail: z.string().email().optional(),
});

type Step1Input = z.infer<typeof step1Schema>;

export default function StoreStep1Page() {
  const params = useParams();
  const locale = params.locale as string;
  const searchParams = useSearchParams();
  const bazaar = searchParams.get('bazaar');
  const t = useTranslations('market.storeWizard.step1');

  return (
    <FormProvider {...useForm<Step1Input>({ resolver: zodResolver(step1Schema), mode: 'onChange' })}>
      <StoreStep1Form locale={locale} />
    </FormProvider>
  );
}