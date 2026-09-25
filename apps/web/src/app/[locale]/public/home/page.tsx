import { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Stat } from '@/components/ui/Stat';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'خانه', en: 'Home' };
  const descriptions: Record<string, string> = {
    fa: 'پلتفرم هوشمند مدیریت منظر',
    en: 'Smart Landscape Management Platform',
  };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/home`,
      title: titles[locale] ?? titles.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/home`,
      languages: { fa: `${BASE_URL}/fa/public/home`, en: `${BASE_URL}/en/public/home` },
    },
  };
}

export default async function HomePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.home');
  const common = await getTranslations('common');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={t('provenanceLabel')}
          label={t('provenanceLabel')}
          verified={false}
          method={t('liveWhenAvailable')}
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
        <h2 className="text-xl font-semibold text-ink mb-4">{t('keyMetrics')}</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Stat
            label={t('beneficiaries')}
            value={t('afterPilot')}
            provenance={{
              source: t('statusSource'),
              verified: false,
              method: t('liveWhenAvailable'),
            }}
          />
          <Stat
            label={t('activeMarkets')}
            value={t('afterPilot')}
            provenance={{
              source: t('statusSource'),
              verified: false,
              method: t('liveWhenAvailable'),
            }}
          />
          <Stat
            label={t('landProfiles')}
            value={t('afterPilot')}
            provenance={{
              source: t('statusSource'),
              verified: false,
              method: t('liveWhenAvailable'),
            }}
          />
          <Stat
            label={t('carbonProjects')}
            value={t('afterPilot')}
            provenance={{
              source: t('statusSource'),
              verified: false,
              method: t('liveWhenAvailable'),
            }}
          />
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('quickActions')}</h2>
        <div className="flex flex-wrap gap-4">
          <Link
            href={`/${locale}/market`}
            className="rounded-[var(--radius-8)] bg-[var(--color-forest)] px-4 py-2 text-sm font-semibold text-[var(--color-paper)] hover:opacity-90"
          >
            {t('enterMarket')}
          </Link>
          <Link
            href={`/${locale}/hydroma`}
            className="rounded-[var(--radius-8)] border border-[var(--color-line)] bg-[var(--color-surface)] px-4 py-2 text-sm font-semibold text-[var(--color-ink)] hover:opacity-90"
          >
            {t('exploreScience')}
          </Link>
          <Link
            href={`/${locale}/public/education/library`}
            className="rounded-[var(--radius-8)] px-4 py-2 text-sm font-semibold text-[var(--color-ink)] hover:opacity-90"
          >
            {t('learnMore')}
          </Link>
        </div>
      </section>
    </main>
  );
}
