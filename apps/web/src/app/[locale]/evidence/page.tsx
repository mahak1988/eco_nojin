import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';

export const dynamic = 'force-dynamic';

export default async function EvidencePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return (
    <main id="main">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 py-10">
        <FivePart
          title={t('evidence.title')}
          lead={t('evidence.lead')}
          what={t('evidence.what')}
          audience={t('evidence.audience')}
          evidence={t.raw('evidence.refs') as string[]}
          limits={t.raw('evidence.limits') as string[]}
          next={t.raw('evidence.next') as string[]}
          evidenceLabel={t('evidence.refsTitle')}
          limitsLabel={t('evidence.limitsTitle')}
          nextLabel={t('evidence.nextTitle')}
        />
        <div className="mt-8">
          <ProvenanceStamp source={t('evidence.refsTitle')}>
            {t('statusLine.realData')}
          </ProvenanceStamp>
        </div>
      </div>
    </main>
  );
}
