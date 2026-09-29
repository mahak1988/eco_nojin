import type { Metadata } from 'next';
import Image from 'next/image';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteFooter } from '@/components/SiteFooter';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { StateSlot } from '@/components/ui/StateSlot';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { Link } from '@/i18n/navigation';
import { apiGet } from '@/lib/api/client';

/**
 * The three reads that let `/about` say something measured rather than only
 * described. All three are published GETs; the page shows each one's state
 * instead of assuming an answer, because an "about" page that silently shows
 * zeros when the gateway is down is worse than one that shows nothing.
 */
const READS = [
  { id: 'models', path: '/api/v1/models' },
  { id: 'tool-registry', path: '/api/v1/tool-registry' },
  { id: 'platform', path: '/api/v1/platform/stats' },
] as const;

type Counted = { count?: number };
type PlatformStats = { total_projects: number | null; total_landscapes: number | null };

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('public.about');

  return {
    title: t('metaTitle'),
    description: t('metaDescription'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/about`,
      title: t('metaTitle'),
      description: t('metaDescription'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/about'),
      languages: languageAlternates('/about'),
    },
  };
}

export default async function AboutPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  await params;
  setRequestLocale(locale);

  const t = await getTranslations('public.about');
  const copy = await getTranslations('about');
  const owner = await getTranslations('owner');
  const statementsCopy = await getTranslations('statements');
  const platformCopy = await getTranslations('platformOverview');
  const servicesCopy = await getTranslations('services');
  const common = await getTranslations('common');
  const statusLine = await getTranslations('statusLine');
  const nf = new Intl.NumberFormat(locale);

  const [models, tools, platform] = await Promise.all([
    apiGet<Counted>(READS[0].path),
    apiGet<Counted>(READS[1].path),
    apiGet<PlatformStats>(READS[2].path),
  ]);

  const results = [models, tools, platform];
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
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <FivePart
          title={t('metaTitle')}
          lead={t('metaDescription')}
          what={copy('what')}
          audience={copy('audience')}
          evidence={copy.raw('evidence') as string[]}
          limits={copy.raw('limits') as string[]}
          next={copy.raw('next') as string[]}
        />

        <section className="mt-10" aria-labelledby="about-state">
          <h2 id="about-state" className="field-label">
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
              detail={`${answered}/${results.length} · ${READS.map((read) => read.path).join(' · ')}`}
            >
              <div className="grid gap-3 sm:grid-cols-3">
                <Card density="compact">
                  <p className="num text-xs text-ink-soft">{READS[0].path}</p>
                  <p className="num mt-2 text-2xl font-semibold text-ink">
                    {models.ok && models.data.count !== undefined
                      ? nf.format(models.data.count)
                      : statusLine('unavailable')}
                  </p>
                  <div className="mt-3 flex items-center justify-between gap-2">
                    <ProvenanceStamp source={READS[0].path} verified={models.ok} />
                    <StatusDot
                      state={models.ok ? 'ok' : 'down'}
                      label={models.ok ? common('live') : statusLine('unavailable')}
                    />
                  </div>
                </Card>
                <Card density="compact">
                  <p className="num text-xs text-ink-soft">{READS[1].path}</p>
                  <p className="num mt-2 text-2xl font-semibold text-ink">
                    {tools.ok && tools.data.count !== undefined
                      ? nf.format(tools.data.count)
                      : statusLine('unavailable')}
                  </p>
                  <div className="mt-3 flex items-center justify-between gap-2">
                    <ProvenanceStamp source={READS[1].path} verified={tools.ok} />
                    <StatusDot
                      state={tools.ok ? 'ok' : 'down'}
                      label={tools.ok ? common('live') : statusLine('unavailable')}
                    />
                  </div>
                </Card>
                <Card density="compact">
                  <p className="num text-xs text-ink-soft">{READS[2].path}</p>
                  <p className="num mt-2 text-2xl font-semibold text-ink">
                    {platform.ok && platform.data.total_projects !== null
                      ? nf.format(platform.data.total_projects)
                      : statusLine('noData')}
                  </p>
                  <div className="mt-3 flex items-center justify-between gap-2">
                    <ProvenanceStamp source={READS[2].path} verified={platform.ok} />
                    <StatusDot
                      state={platform.ok ? 'ok' : 'down'}
                      label={platform.ok ? common('live') : statusLine('unavailable')}
                    />
                  </div>
                </Card>
              </div>
            </StateSlot>
          </div>
        </section>

        <section className="panel mt-10 p-6" aria-labelledby="owner-heading">
          <h2 id="owner-heading" className="text-sm font-semibold text-[var(--ink-soft)]">
            {owner('sectionTitle')}
          </h2>
          <div className="mt-4 flex flex-wrap items-center gap-6">
            <Image
              src="/brand/owner-narvan-logo-transparent.png"
              alt={owner('logoAlt')}
              width={848}
              height={1020}
              className="h-20 w-auto"
            />
            <div className="max-w-md">
              <p className="text-sm font-semibold text-[var(--ink)]">{owner('role')}</p>
              <p className="mt-1 text-sm text-[var(--ink-soft)]">{owner('statement')}</p>
            </div>
          </div>
        </section>

        <nav className="mt-10 flex flex-wrap gap-3">
          <Link href="/statements" className="btn btn-ghost">
            {statementsCopy('title')}
          </Link>
          <Link href="/platform" className="btn btn-ghost">
            {platformCopy('title')}
          </Link>
          <Link href="/services" className="btn btn-ghost">
            {servicesCopy('title')}
          </Link>
        </nav>
      </div>
      <SiteFooter />
    </main>
  );
}
