import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { StateSlot } from '@/components/ui/StateSlot';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';

const PILOT_PATH = '/api/v1/pilot/stats';
const MODELS_PATH = '/api/v1/models';
const PLATFORM_PATH = '/api/v1/platform/stats';

type PilotStats = {
  applications: number;
  provinces: number;
  total_hectares: number;
  status: string;
  /** The gateway's own word for what it has not measured. */
  outcomes_status: string;
  generated_at: string;
};

type ModelsIndex = { count: number };

type PlatformStats = { total_landscapes: number | null; total_projects: number | null };

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.statement');

  return {
    title: t('metaTitle'),
    description: t('metaDescription'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/statements`,
      title: t('metaTitle'),
      description: t('metaDescription'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/statements'),
      languages: languageAlternates('/statements'),
    },
  };
}

export default async function StatementsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  const t = await getTranslations('public.statement');
  const copy = await getTranslations('statements');
  const common = await getTranslations('common');
  const statusLine = await getTranslations('statusLine');
  const nf = new Intl.NumberFormat(locale);

  /**
   * The three reads a statement page may quote.
   *
   * `pilot.py:73` returns `outcomes_status: "awaiting_verified_data"` and
   * `pilot.py:76` says in its own docstring that these are application
   * aggregates and not outcomes. So the numbers are rendered with the gateway's
   * own caveat attached, and the impact claim this page is really about is left
   * explicitly unclaimed rather than approximated from an application count.
   */
  const [pilot, models, platform] = await Promise.all([
    apiGet<PilotStats>(PILOT_PATH),
    apiGet<ModelsIndex>(MODELS_PATH),
    apiGet<PlatformStats>(PLATFORM_PATH),
  ]);

  const results = [pilot, models, platform];
  const answered = results.filter((result) => result.ok).length;
  const state = (() => {
    if (answered === results.length) return 'ready' as const;
    if (answered === 0) {
      return results.every((result) => !result.ok && result.status === 0)
        ? ('offline' as const)
        : ('error' as const);
    }
    return 'partial' as const;
  })();

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <article className="mx-auto max-w-3xl px-6 pb-16 pt-8">
        <header>
          <h1 className="display text-3xl font-bold text-balance text-ink sm:text-4xl">
            {t('metaTitle')}
          </h1>
          <p className="mt-3 text-ink-soft">{t('metaDescription')}</p>
        </header>

        <section className="card mt-6 p-6">
          <h2 className="field-label">{copy('missionTitle')}</h2>
          <p className="mt-3 text-sm leading-relaxed text-ink">{copy('missionBody')}</p>
        </section>

        <section className="mt-8" aria-labelledby="statements-figures">
          <h2 id="statements-figures" className="field-label">
            {t('metaTitle')}
          </h2>
          <div className="mt-3">
            <StateSlot
              state={state}
              density="compact"
              labels={{
                loading: common('retry'),
                empty: statusLine('noData'),
                error: statusLine('unavailable'),
                partial: statusLine('realData'),
                offline: statusLine('unavailable'),
              }}
              detail={`${answered}/${results.length} · ${PILOT_PATH} · ${MODELS_PATH} · ${PLATFORM_PATH}`}
            >
              <div className="grid gap-3 sm:grid-cols-3">
                <Card density="compact">
                  <p className="num text-xs text-ink-soft">{PILOT_PATH} · applications</p>
                  <p className="num mt-2 text-3xl font-semibold text-ink">
                    {pilot.ok ? nf.format(pilot.data.applications) : statusLine('unavailable')}
                  </p>
                  {pilot.ok ? (
                    <p className="num mt-1 text-xs text-copper">{pilot.data.outcomes_status}</p>
                  ) : null}
                  <div className="mt-3">
                    <ProvenanceStamp source={PILOT_PATH} verified={pilot.ok} />
                  </div>
                </Card>
                <Card density="compact">
                  <p className="num text-xs text-ink-soft">{MODELS_PATH}</p>
                  <p className="num mt-2 text-3xl font-semibold text-ink">
                    {models.ok ? nf.format(models.data.count) : statusLine('unavailable')}
                  </p>
                  <div className="mt-3">
                    <ProvenanceStamp source={MODELS_PATH} verified={models.ok} />
                  </div>
                </Card>
                <Card density="compact">
                  <p className="num text-xs text-ink-soft">{PLATFORM_PATH} · projects</p>
                  <p className="num mt-2 text-3xl font-semibold text-ink">
                    {platform.ok && platform.data.total_projects !== null
                      ? nf.format(platform.data.total_projects)
                      : statusLine('noData')}
                  </p>
                  <div className="mt-3">
                    <ProvenanceStamp source={PLATFORM_PATH} verified={platform.ok} />
                  </div>
                </Card>
              </div>
            </StateSlot>
          </div>
        </section>

        <section className="mt-8" aria-labelledby="statements-unclaimed">
          <h2 id="statements-unclaimed" className="field-label">
            {t('aspirationTitle')}
          </h2>
          <Card density="cozy" className="mt-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <StatusDot state="warn" label={t('aspirationTitle')} />
              <ProvenanceStamp source={PILOT_PATH} verified={false} method="outcomes_status" />
            </div>
            <p className="mt-3 text-sm text-ink-soft">{t('aspirationBody')}</p>
          </Card>
        </section>

        <blockquote className="mt-8 border-s-2 border-water/60 ps-4">
          <p className="text-sm text-ink-soft">{copy('quoteLabel')}</p>
        </blockquote>

        <section className="card mt-8 p-6">
          <h2 className="field-label">{copy('transparencyTitle')}</h2>
          <p className="mt-3 text-sm text-ink">{copy('transparencyBody')}</p>
        </section>
      </article>
    </main>
  );
}
