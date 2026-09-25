import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { apiGet } from '@/lib/api/client';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

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
  const template = await getTranslations('market.template');

  const path = `/api/v1/legal-texts/${locale}/${SLUG}`;
  const record = await apiGet<LegalText>(path);
  const legalText = record.ok ? record.data : null;
  const published = legalText?.status === 'published';
  const heading = legalText?.title ?? TITLES[locale] ?? TITLES.en;

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
    </main>
  );
}
