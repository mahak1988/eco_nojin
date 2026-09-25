import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

const MODEL_CARDS_PATH = '/api/v1/science/model-cards';

type ModelCard = {
  validity: string;
  limitations: string;
};

type ModelCardEntry = {
  slug: string;
  card: ModelCard;
  fidelity: string | null;
  domain: string | null;
};

type ModelCards = {
  count: number;
  cards: ModelCardEntry[];
};

const TITLES: Record<string, string> = { fa: 'محدودیت‌ها', en: 'Limitations' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'محدودیت‌های شناخته‌شده مدل‌ها و داده‌ها',
  en: 'Known limitations of models and data',
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
      url: `${BASE_URL}/${locale}/public/science/limitations`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/science/limitations`,
      languages: {
        fa: `${BASE_URL}/fa/public/science/limitations`,
        en: `${BASE_URL}/en/public/science/limitations`,
      },
    },
  };
}

export default async function LimitationsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('statusLine');
  const template = await getTranslations('market.template');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  const cards = await apiGet<ModelCards>(MODEL_CARDS_PATH);
  const entries = (cards.ok ? cards.data.cards : []).filter(
    (entry) => entry.card?.limitations || entry.card?.validity,
  );

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={MODEL_CARDS_PATH}
          label={title}
          verified={cards.ok}
          method={MODEL_CARDS_PATH}
        >
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{template('source')}</h2>
        {entries.length === 0 ? (
          <Card density="compact">
            <h3 className="text-sm font-medium text-ink">{template('unavailableTitle')}</h3>
            <p className="mt-1 text-sm text-ink-soft">{template('unavailableDescription')}</p>
            <p className="mt-3 text-xs text-ink-soft">
              {t('unavailable')}
              {cards.ok ? '' : ` · ${cards.error}`}
            </p>
          </Card>
        ) : (
          <>
            <div className="grid gap-4">
              {entries.map((entry) => (
                <Card key={entry.slug} density="compact">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <h3 className="font-mono text-sm font-medium text-ink">{entry.slug}</h3>
                      {entry.card.validity ? (
                        <p className="mt-1 text-sm text-ink-soft">{entry.card.validity}</p>
                      ) : null}
                      {entry.card.limitations ? (
                        <p className="mt-1 text-sm text-ink-soft">{entry.card.limitations}</p>
                      ) : null}
                    </div>
                    <ProvenanceStamp
                      source={MODEL_CARDS_PATH}
                      verified={false}
                      method={entry.domain ?? undefined}
                      label={entry.fidelity ?? undefined}
                    />
                  </div>
                </Card>
              ))}
            </div>
            <p className="mt-6 text-xs text-ink-soft">
              {MODEL_CARDS_PATH} · {t('realData')}
            </p>
          </>
        )}
      </section>
    </main>
  );
}
