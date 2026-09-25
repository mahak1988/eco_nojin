import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const CONTENT_SEARCH_PATH = '/api/v1/content/search';

type ContentHit = {
  id: string;
  title: string;
  category: string;
  language: string;
  published_at: string | null;
  snippet: string;
};

type ContentSearch = {
  query: string;
  count: number;
  results: ContentHit[];
};

const TITLES: Record<string, string> = { fa: 'کتابخانه آموزشی', en: 'Education Library' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'مجموعه راهنماها، ویدئوها و مقالات',
  en: 'Guides, videos, and articles collection',
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
      url: `${BASE_URL}/${locale}/public/education/library`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/education/library`,
      languages: {
        fa: `${BASE_URL}/fa/public/education/library`,
        en: `${BASE_URL}/en/public/education/library`,
      },
    },
  };
}

export default async function LibraryPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');
  const learn = await getTranslations('learn');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  // The library only exposes published content through the RAG search surface;
  // there is no unfiltered listing endpoint, so nothing is invented here.
  const content = await apiGet<ContentSearch>(CONTENT_SEARCH_PATH);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={CONTENT_SEARCH_PATH}
          label={title}
          verified={content.ok}
          method={CONTENT_SEARCH_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{template('source')}</h2>
        <Card density="compact">
          <h3 className="text-sm font-medium text-ink">
            {content.ok ? learn('emptyTitle') : template('unavailableTitle')}
          </h3>
          <p className="mt-1 text-sm text-ink-soft">
            {content.ok ? learn('emptyDesc') : template('unavailableDescription')}
          </p>
          <p className="mt-3 text-xs text-ink-soft">
            {CONTENT_SEARCH_PATH} · {t('unavailable')}
            {content.ok ? '' : ` · ${content.error}`}
          </p>
        </Card>
        <p className="mt-6 text-xs text-ink-soft">{t('realData')}</p>
      </section>
    </main>
  );
}
