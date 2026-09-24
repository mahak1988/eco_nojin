import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { SiteNav } from '@/components/SiteNav';

export const dynamic = 'force-dynamic';

export default async function AiPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return (
    <main id="main">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 py-10">
        <FivePart
          title={t('ai.title')}
          lead={t('ai.lead')}
          what={t('ai.what')}
          audience={t('ai.audience')}
          evidence={[t('ai.sourceRule')]}
          limits={t.raw('ai.limits') as string[]}
          next={t.raw('ai.next') as string[]}
          limitsLabel={t('ai.limitsTitle')}
          nextLabel={t('ai.nextTitle')}
        />
      </div>
    </main>
  );
}
