import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { SiteNav } from '@/components/SiteNav';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('services');
  return {
    title: t('title'),
    description: t('lead'),
  };
}

export default async function ServicesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return (
    <main id="main">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 py-10">
        <FivePart
          title={t('services.title')}
          lead={t('services.lead')}
          what={t('services.what')}
          audience={t('services.audience')}
          evidence={t.raw('services.evidence') as string[]}
          limits={t.raw('services.limits') as string[]}
          next={t.raw('services.next') as string[]}
        />
      </div>
    </main>
  );
}
