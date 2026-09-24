import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Stat } from '@/components/ui/Stat';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'کشاورزان', en: 'Farmers' };
  const descriptions: Record<string, string> = { fa: 'راهکارها برای کشاورزان کوچک و متوسط', en: 'Solutions for small and medium farmers' };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: { type: 'website', locale, url: `${BASE_URL}/${locale}/public/audiences/farmers`, title: titles[locale] ?? titles.en },
    alternates: { canonical: `${BASE_URL}/${locale}/public/audiences/farmers`, languages: { fa: `${BASE_URL}/fa/public/audiences/farmers`, en: `${BASE_URL}/en/public/audiences/farmers` } },
  };
}

export default async function FarmersPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.audiences.farmers');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="User Research" label={t('provenanceLabel')} verified={true} method="Field interviews" timestamp="2024-12-01">
          <h1 className="display text-4xl font-bold text-ink">{t('title')}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <FivePart
          title={t('whatTitle')}
          lead={t('whatLead')}
          what={t('whatDesc')}
          audience={t('audience')}
          evidence={['500+ farmer interviews', 'Pilot village data', 'Cooperative feedback']}
          limits={['Literacy variations', 'Connectivity gaps', 'Seasonal workflow']}
          next={['Add voice-first UI', 'Offline data entry', 'SMS alerts']}
          evidenceLabel={common('evidence')} limitsLabel={common('limits')} nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('solutions')}</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Card density="cozy">
            <h3 className="font-semibold text-ink mb-2">{t('sol1_title')}</h3>
            <p className="text-ink-soft mb-4">{t('sol1_desc')}</p>
            <Button variant="primary" size="sm">{t('tryNow')}</Button>
          </Card>
          <Card density="cozy">
            <h3 className="font-semibold text-ink mb-2">{t('sol2_title')}</h3>
            <p className="text-ink-soft mb-4">{t('sol2_desc')}</p>
            <Button variant="primary" size="sm">{t('tryNow')}</Button>
          </Card>
          <Card density="cozy">
            <h3 className="font-semibold text-ink mb-2">{t('sol3_title')}</h3>
            <p className="text-ink-soft mb-4">{t('sol3_desc')}</p>
            <Button variant="primary" size="sm">{t('tryNow')}</Button>
          </Card>
        </div>
      </section>
    </main>
  );
}