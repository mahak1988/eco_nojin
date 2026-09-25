import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const TITLES: Record<string, string> = { fa: 'برنامه‌های گواهی', en: 'Certification Programs' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'مسیرهای تخصصی با گواهی‌نامه',
  en: 'Specialized pathways with certification',
};

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  return {
    title: TITLES[locale] ?? TITLES.en,
    description: DESCRIPTIONS[locale] ?? DESCRIPTIONS.en,
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/education/certifications`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/education/certifications`,
      languages: {
        fa: `${BASE_URL}/fa/public/education/certifications`,
        en: `${BASE_URL}/en/public/education/certifications`,
      },
    },
  };
}

export default async function CertificationsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');
  const learn = await getTranslations('learn');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={template('source')}
          label={title}
          verified={false}
          method={template('method')}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{template('contractTitle')}</h2>
        <Card density="compact">
          <h3 className="text-sm font-medium text-ink">{learn('emptyTitle')}</h3>
          <p className="mt-1 text-sm text-ink-soft">{learn('emptyDesc')}</p>
          <p className="mt-3 text-xs text-ink-soft">
            {template('method')} · {t('unavailable')}
          </p>
        </Card>
        <p className="mt-6 text-xs text-ink-soft">{t('realData')}</p>
      </section>
    </main>
  );
}
