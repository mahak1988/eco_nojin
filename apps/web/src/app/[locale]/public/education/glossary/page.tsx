import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const AGROVOC_PATH = '/api/v1/science/agrovoc';

type AgrovocEntry = {
  term: string;
  term_en: string;
  uri: string;
  group: string;
  aliases: string[];
};

type AgrovocResult = {
  count: number | null;
  results: AgrovocEntry[];
  stats: Record<string, number>;
};

const TITLES: Record<string, string> = { fa: 'واژه‌نامه دوزبانه', en: 'Bilingual Glossary' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'واژه‌نامه تخصصی قابل جستجو',
  en: 'Searchable bilingual technical glossary',
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
      url: `${BASE_URL}/${locale}/public/education/glossary`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/education/glossary`,
      languages: {
        fa: `${BASE_URL}/fa/public/education/glossary`,
        en: `${BASE_URL}/en/public/education/glossary`,
      },
    },
  };
}

export default async function GlossaryPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');
  const learn = await getTranslations('learn');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  // The gateway exposes a curated bilingual term map through AGROVOC search;
  // an empty query returns the real concept counts per group.
  const glossary = await apiGet<AgrovocResult>(AGROVOC_PATH);
  const terms = glossary.ok ? glossary.data.results : [];
  const stats = glossary.ok ? glossary.data.stats : {};

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={AGROVOC_PATH}
          label={title}
          verified={glossary.ok}
          method={AGROVOC_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{AGROVOC_PATH}</h2>
        {!glossary.ok ? (
          <Card density="compact">
            <h3 className="text-sm font-medium text-ink">{template('unavailableTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{template('unavailableDescription')}</p>
            <p className="mt-3 text-xs text-ink-soft">
              {t('unavailable')} · {glossary.error}
            </p>
          </Card>
        ) : terms.length === 0 ? (
          <>
            <Card density="compact">
              <h3 className="text-sm font-medium text-ink">{learn('emptyTitle')}</h3>
              <p className="mt-1 text-sm text-ink-soft">{learn('emptyDesc')}</p>
            </Card>
            <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {Object.entries(stats).map(([group, count]) => (
                <Card key={group} density="compact">
                  <div className="num text-2xl font-semibold text-ink">{count}</div>
                  <p className="mt-1 text-sm text-ink-soft">{group}</p>
                </Card>
              ))}
            </div>
            <p className="mt-6 text-xs text-ink-soft">
              {AGROVOC_PATH} · {t('realData')}
            </p>
          </>
        ) : (
          <>
            <div className="grid gap-4">
              {terms.map((entry) => (
                <Card key={entry.uri} density="compact">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <h3 className="font-medium text-ink">
                        {locale === 'fa' ? entry.term : entry.term_en}
                      </h3>
                      <p className="mt-1 text-sm text-ink-soft">{entry.aliases.join(' · ')}</p>
                    </div>
                    <ProvenanceStamp
                      source={entry.uri}
                      verified={false}
                      method={entry.group}
                      label={entry.group}
                    />
                  </div>
                </Card>
              ))}
            </div>
            <p className="mt-6 text-xs text-ink-soft">
              {AGROVOC_PATH} · {t('realData')}
            </p>
          </>
        )}
      </section>
    </main>
  );
}
