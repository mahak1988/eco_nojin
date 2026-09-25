import type { Metadata } from 'next';

import { SustainabilityDashboardPrototype } from '@/components/SustainabilityDashboardPrototype';

export const metadata: Metadata = {
  title: 'Eco Nojin | Sustainability Intelligence Prototype',
  description:
    'A living prototype for evidence-led water, soil, climate, biodiversity, and sustainability intelligence.',
};

export default async function PrototypePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;

  return <SustainabilityDashboardPrototype locale={locale} />;
}
