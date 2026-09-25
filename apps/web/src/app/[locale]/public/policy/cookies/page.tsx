import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet } from '@/lib/api/client';
import { DataStateCard, SourceFooter, toDataState } from '../../data-states';

const SLUGS_PATH = '/api/v1/legal-texts/slugs';
const LOCALES_PATH = '/api/v1/legal-texts/locales';
const SLUG = 'cookies';

const TITLES: Record<string, string> = { fa: 'سیاست کوکی', en: 'Cookie Policy' };
const DESCRIPTIONS: Record<string, string> = {
  fa: 'متن سیاست کوکی از سند منتشرشده در سرویس متن‌های حقوقی خوانده می‌شود.',
  en: 'The cookie policy text is read from the published legal-texts record.',
};

type LegalText = {
  id: string;
  locale: string;
  slug: string;
  title: string;
  body: string;
  version: number;
  status: string;
  effective_at: string | null;
  created_at: string | null;
  updated_at: string | null;
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
      url: `${BASE_URL}/${locale}/public/policy/cookies`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/policy/cookies`,
      languages: {
        fa: `${BASE_URL}/fa/public/policy/cookies`,
        en: `${BASE_URL}/en/public/policy/cookies`,
      },
    },
  };
}

export default async function CookiesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const status = await getTranslations('statusLine');
  const common = await getTranslations('common');
  const template = await getTranslations('market.template');

  const path = `/api/v1/legal-texts/${locale}/${SLUG}`;
  const [record, slugs, locales] = await Promise.all([
    apiGet<LegalText>(path),
    apiGet<string[]>(SLUGS_PATH),
    apiGet<string[]>(LOCALES_PATH),
  ]);
  const legalText = record.ok ? record.data : null;
  const published = legalText?.status === 'published';
  const heading = legalText?.title ?? TITLES[locale] ?? TITLES.en;
  const slugRows = slugs.ok ? slugs.data : [];
  const localeRows = locales.ok ? locales.data : [];
  const slugsState = toDataState(SLUGS_PATH, slugs, slugRows.length);
  const localesState = toDataState(LOCALES_PATH, locales, localeRows.length);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <ProvenanceStamp
          source={path}
          label={heading}
          verified={published}
          method={path}
          timestamp={legalText?.updated_at ?? undefined}
        >
          <h1 className="display text-4xl font-bold text-ink">{heading}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{DESCRIPTIONS[locale] ?? DESCRIPTIONS.en}</p>

        {legalText ? (
          <>
            <div className="mt-6">
              <StatusDot state={published ? 'ok' : 'warn'} label={legalText.status} />
            </div>
            <Card density="cozy" className="mt-6">
              <dl className="grid gap-4 text-sm sm:grid-cols-3">
                <div>
                  <dt className="field-label">version</dt>
                  <dd className="num mt-1 font-mono text-ink">{legalText.version}</dd>
                </div>
                <div>
                  <dt className="field-label">status</dt>
                  <dd className="mt-1 font-mono text-ink">{legalText.status}</dd>
                </div>
                <div>
                  <dt className="field-label">effective_at</dt>
                  <dd className="num mt-1 font-mono text-ink">{legalText.effective_at ?? '—'}</dd>
                </div>
              </dl>
              <div className="prose mt-6 max-w-none whitespace-pre-wrap text-ink-soft">
                {legalText.body}
              </div>
            </Card>
          </>
        ) : (
          <Card density="cozy" className="mt-6">
            <StatusDot state="down" label={status('unavailable')} />
            <h2 className="mt-4 font-semibold text-ink">{template('unavailableTitle')}</h2>
            <p className="mt-2 text-sm text-ink-soft">{template('unavailableDescription')}</p>
            <p className="mt-3 text-xs text-ink-soft">
              {path} · {record.ok ? '' : record.error}
            </p>
          </Card>
        )}
      </div>

      <section className="mx-auto max-w-4xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{common('view')}</h2>
        <DataStateCard state={slugsState} />
        {slugsState.kind === 'ready' && slugs.ok ? (
          <div className="flex flex-wrap gap-2">
            {slugRows.map((slug) => (
              <span key={slug} className="rounded bg-forest/10 px-2 py-1 text-xs text-forest">
                {slug}
              </span>
            ))}
          </div>
        ) : null}
        <SourceFooter state={slugsState} />
        <h2 className="mt-8 text-xl font-semibold text-ink mb-4">{LOCALES_PATH}</h2>
        <DataStateCard state={localesState} />
        {localesState.kind === 'ready' && locales.ok ? (
          <div className="flex flex-wrap gap-2">
            {localeRows.map((entry) => (
              <span key={entry} className="rounded bg-forest/10 px-2 py-1 text-xs text-forest">
                {entry}
              </span>
            ))}
          </div>
        ) : null}
        <SourceFooter state={localesState} />
      </section>
    </main>
  );
}
