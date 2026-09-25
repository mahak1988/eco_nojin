import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const MODEL_CARDS_PATH = '/api/v1/science/model-cards';

type ModelCard = { validity?: string; limitations?: string };

type ModelCardEntry = {
  slug: string;
  card: ModelCard;
  fidelity: string | null;
  domain: string | null;
};

type ModelCards = { count: number; cards: ModelCardEntry[] };

const TITLES: Record<string, string> = { fa: 'تحلیل شکاف', en: 'Gap Analysis' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'دامنهٔ اعتبار و محدودیت ثبت‌شدهٔ هر مدل در رجیستری',
  en: 'Registered validity domain and limitations per model',
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
      url: `${BASE_URL}/${locale}/public/science/gap-analysis`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/science/gap-analysis`,
      languages: {
        fa: `${BASE_URL}/fa/public/science/gap-analysis`,
        en: `${BASE_URL}/en/public/science/gap-analysis`,
      },
    },
  };
}

export default async function GapAnalysisPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const status = await getTranslations('statusLine');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  const cards = await apiGet<ModelCards>(MODEL_CARDS_PATH);
  const entries = cards.ok
    ? cards.data.cards.filter((entry) => entry.card?.limitations || entry.card?.validity)
    : [];
  const state = toDataState(MODEL_CARDS_PATH, cards, entries.length);

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
        <h2 className="text-xl font-semibold text-ink mb-4">{MODEL_CARDS_PATH}</h2>
        <DataStateCard state={state} />
        {state.kind === 'ready' ? (
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
                  <div className="flex items-center gap-3">
                    <StatusDot
                      state={entry.fidelity === 'official' ? 'ok' : 'warn'}
                      label={entry.fidelity ?? status('unavailable')}
                    />
                    <ProvenanceStamp
                      source={MODEL_CARDS_PATH}
                      verified={false}
                      method={entry.domain ?? undefined}
                    />
                  </div>
                </div>
              </Card>
            ))}
          </div>
        ) : null}
        <SourceFooter state={state} />
      </section>
    </main>
  );
}
