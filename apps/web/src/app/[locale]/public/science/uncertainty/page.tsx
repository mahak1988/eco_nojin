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
const VALIDATION_PATH = '/api/v1/hydroma/validation';

type ModelCard = { validity?: string; limitations?: string };

type ModelCardEntry = {
  slug: string;
  card: ModelCard;
  fidelity: string | null;
  domain: string | null;
};

type ModelCards = { count: number; cards: ModelCardEntry[] };

type ValidationReport = {
  total: number;
  passed: number;
  failed: number;
  pass_rate: number;
};

const TITLES: Record<string, string> = { fa: 'عدم‌قطعیت', en: 'Uncertainty' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'محدودیت‌های اعلام‌شده و وضعیت واقعی بررسی فرمول‌ها',
  en: 'Declared limitations and the real formula-verification status',
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
      url: `${BASE_URL}/${locale}/public/science/uncertainty`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/science/uncertainty`,
      languages: {
        fa: `${BASE_URL}/fa/public/science/uncertainty`,
        en: `${BASE_URL}/en/public/science/uncertainty`,
      },
    },
  };
}

export default async function UncertaintyPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const status = await getTranslations('statusLine');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  // No posterior or confidence-interval distribution is served by the gateway;
  // the honest uncertainty surface is the declared model-card limitation plus the
  // executed formula-check pass rate.
  const [cards, report] = await Promise.all([
    apiGet<ModelCards>(MODEL_CARDS_PATH),
    apiGet<ValidationReport>(VALIDATION_PATH),
  ]);
  const entries = cards.ok ? cards.data.cards.filter((entry) => entry.card?.limitations) : [];
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

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <h2 className="text-xl font-semibold text-ink mb-4">{VALIDATION_PATH}</h2>
        {report.ok ? (
          <Card density="compact">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="num text-sm text-ink">
                {report.data.total} · {report.data.passed} · {report.data.failed} ·{' '}
                {report.data.pass_rate}
              </p>
              <StatusDot
                state={report.data.failed === 0 ? 'ok' : 'warn'}
                label={report.data.failed === 0 ? status('realData') : status('unavailable')}
              />
            </div>
            <div className="mt-3">
              <ProvenanceStamp source={VALIDATION_PATH} verified method={VALIDATION_PATH} />
            </div>
          </Card>
        ) : (
          <Card density="compact">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-sm font-medium text-ink">{status('unavailable')}</h3>
              <StatusDot state="down" label={status('unavailable')} />
            </div>
            <p className="mt-1 text-sm text-ink-soft">
              {VALIDATION_PATH} · {report.error}
            </p>
            <div className="mt-3">
              <ProvenanceStamp source={VALIDATION_PATH} verified={false} method={VALIDATION_PATH} />
            </div>
          </Card>
        )}
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
                    <p className="mt-1 text-sm text-ink-soft">{entry.card.limitations}</p>
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
        ) : null}
        <SourceFooter state={state} />
      </section>
    </main>
  );
}
