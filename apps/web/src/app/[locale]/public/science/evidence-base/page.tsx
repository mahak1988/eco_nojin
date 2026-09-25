import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const CITATIONS_PATH = '/api/v1/science/citations/index';

type CitationItem = {
  slug: string;
  name_fa: string;
  name_en: string;
  reference: string;
  citation: string;
  doi: string | null;
  note: string;
};

type CitationIndex = {
  count: number;
  items: CitationItem[];
};

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const titles: Record<string, string> = { fa: 'پایه‌های علمی', en: 'Scientific Evidence Base' };
  const descriptions: Record<string, string> = {
    fa: 'مجموعه شواهد علمی با DOI و وضعیت تأیید',
    en: 'Curated scientific evidence with DOI and verification status',
  };
  return {
    title: titles[locale] ?? titles.en,
    description: descriptions[locale] ?? descriptions.en,
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/science/evidence-base`,
      title: titles[locale] ?? titles.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/science/evidence-base`,
      languages: {
        fa: `${BASE_URL}/fa/public/science/evidence-base`,
        en: `${BASE_URL}/en/public/science/evidence-base`,
      },
    },
  };
}

export default async function EvidenceBasePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.science.evidenceBase');
  const common = await getTranslations('common');
  const status = await getTranslations('statusLine');

  const citations = await apiGet<CitationIndex>(CITATIONS_PATH);
  const items = citations.ok ? citations.data.items : [];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={CITATIONS_PATH}
          label={t('provenanceLabel')}
          verified={citations.ok}
          method={CITATIONS_PATH}
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
          evidenceLabel={common('evidenceLabel')}
          limitsLabel={common('limitsLabel')}
          nextLabel={common('nextLabel')}
        />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{t('evidenceCatalog')}</h2>
        {items.length === 0 ? (
          <Card density="compact">
            <h3 className="text-sm font-medium text-ink">{t('emptyTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{t('emptyDesc')}</p>
            <div className="mt-3">
              <StatusDot state="down" label={citations.ok ? '—' : citations.error} />
            </div>
          </Card>
        ) : (
          <div className="grid gap-4">
            {items.map((item) => (
              <Card key={item.slug} density="compact">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h3 className="font-medium text-ink">
                      {locale === 'fa' ? item.name_fa : item.name_en}
                    </h3>
                    <p className="mt-1 text-sm text-ink-soft">{item.reference}</p>
                    <p className="mt-1 text-xs text-ink-soft">{item.citation}</p>
                    <p className="mt-1 text-xs text-ink-soft">
                      DOI:{' '}
                      {item.doi ? (
                        <code className="font-mono">{item.doi}</code>
                      ) : (
                        <span>{status('unavailable')}</span>
                      )}
                    </p>
                    {item.note ? <p className="mt-1 text-xs text-ink-soft">{item.note}</p> : null}
                  </div>
                  <ProvenanceStamp
                    source={item.reference}
                    verified={false}
                    method={item.slug}
                    label={item.doi ? item.doi : undefined}
                  />
                </div>
              </Card>
            ))}
          </div>
        )}
        <p className="mt-6 text-xs text-ink-soft">
          {CITATIONS_PATH} · {status('realData')}
        </p>
      </section>
    </main>
  );
}
