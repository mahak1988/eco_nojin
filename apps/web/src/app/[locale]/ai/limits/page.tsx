import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { SiteNav } from '@/components/SiteNav';

export const dynamic = 'force-dynamic';

export default async function LimitsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('ai');

  return (
    <main id="main">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 py-10">
        <FivePart
          title={t('title')}
          lead={t('lead')}
          what={t('what')}
          audience={t('audience')}
          evidence={t.raw('evidence') as string[]}
          limits={t.raw('limits') as string[]}
          next={t.raw('next') as string[]}
        />
      </div>
    </main>
  );
}
