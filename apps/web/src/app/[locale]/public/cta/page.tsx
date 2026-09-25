import { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'دعوت به اقدام', en: 'Call to Action' };
  const descriptions: Record<string, string> = {
    fa: 'CTAهای اصلی برای ورود به اکوسیستم',
    en: 'Primary CTAs to enter the ecosystem',
  };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/cta`,
      title: titles[locale] ?? titles.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/cta`,
      languages: { fa: `${BASE_URL}/fa/public/cta`, en: `${BASE_URL}/en/public/cta` },
    },
  };
}

export default async function CTAPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.cta');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={t('provenanceLabel')}
          label={t('provenanceLabel')}
          verified={false}
          method={t('provenanceLabel')}
        >
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
          evidence={t.raw('evidenceItems') as string[]}
          limits={t.raw('limitsItems') as string[]}
          next={t.raw('nextItems') as string[]}
          evidenceLabel={common('evidence')}
          limitsLabel={common('limits')}
          nextLabel={common('next')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('primaryCTAs')}</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Card density="cozy" className="text-center">
            <h3 className="font-semibold text-ink mb-2">{t('cta1_title')}</h3>
            <p className="text-ink-soft mb-4">{t('cta1_desc')}</p>
            <Link
              href={`/${locale}/market`}
              className="inline-flex rounded-[var(--radius-8)] bg-[var(--color-forest)] px-4 py-2 font-semibold text-[var(--color-paper)]"
            >
              {t('cta1_action')}
            </Link>
          </Card>
          <Card density="cozy" className="text-center">
            <h3 className="font-semibold text-ink mb-2">{t('cta2_title')}</h3>
            <p className="text-ink-soft mb-4">{t('cta2_desc')}</p>
            <Link
              href={`/${locale}/hydroma`}
              className="inline-flex rounded-[var(--radius-8)] border border-[var(--color-line)] px-4 py-2 font-semibold text-[var(--color-ink)]"
            >
              {t('cta2_action')}
            </Link>
          </Card>
          <Card density="cozy" className="text-center">
            <h3 className="font-semibold text-ink mb-2">{t('cta3_title')}</h3>
            <p className="text-ink-soft mb-4">{t('cta3_desc')}</p>
            <Link
              href={`/${locale}/public/education/library`}
              className="inline-flex rounded-[var(--radius-8)] px-4 py-2 font-semibold text-[var(--color-ink)]"
            >
              {t('cta3_action')}
            </Link>
          </Card>
          <Card density="cozy" className="text-center">
            <h3 className="font-semibold text-ink mb-2">{t('cta4_title')}</h3>
            <p className="text-ink-soft mb-4">{t('cta4_desc')}</p>
            <Link
              href={`/${locale}/public/policy/terms`}
              className="inline-flex rounded-[var(--radius-8)] px-4 py-2 font-semibold text-[var(--color-ink)]"
            >
              {t('cta4_action')}
            </Link>
          </Card>
        </div>
      </section>
    </main>
  );
}
