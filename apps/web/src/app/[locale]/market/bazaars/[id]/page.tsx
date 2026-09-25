import type { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { BAZAARS_SOURCE, getBazaar } from '@/lib/api/market';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.bazaar');
  return {
    title: t('detailTitle'),
    description: t('lead'),
    robots: { index: false, follow: true },
  };
}

export default async function BazaarDetailPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.bazaar');
  const common = await getTranslations('common');
  const statusLine = await getTranslations('statusLine');
  const result = await getBazaar(id);
  const source = `${BAZAARS_SOURCE}/${encodeURIComponent(id)}`;

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <Link href={`/${locale}/market/bazaars`} className="text-sm text-ink-soft underline">
          {common('back')}
        </Link>
        <header className="mt-6 flex flex-wrap items-start gap-4">
          <div className="flex-1">
            <h1 className="display text-balance text-4xl font-bold text-ink">
              {result.ok ? result.data.name : t('detailTitle')}
            </h1>
            {result.ok ? <p className="mt-3 text-ink-soft">{result.data.description}</p> : null}
          </div>
          {result.ok ? (
            <StatusDot
              state={result.data.status === 'approved' ? 'ok' : 'warn'}
              label={result.data.status}
            />
          ) : null}
        </header>

        <div className="mt-5">
          <ProvenanceStamp
            source={source}
            label={t('source')}
            method={result.ok ? statusLine('realData') : statusLine('unavailable')}
          />
        </div>

        {!result.ok ? (
          <Card density="cozy" className="mt-6">
            <p className="text-sm text-clay">{result.error}</p>
          </Card>
        ) : (
          <>
            <Card density="cozy" className="mt-6">
              <dl className="grid gap-4 sm:grid-cols-2">
                <div>
                  <dt className="text-sm text-ink-soft">{t('type')}</dt>
                  <dd className="mt-1 font-medium text-ink">{result.data.marketplace_type}</dd>
                </div>
                <div>
                  <dt className="text-sm text-ink-soft">{t('status')}</dt>
                  <dd className="mt-1 font-medium text-ink">{result.data.status}</dd>
                </div>
                <div>
                  <dt className="text-sm text-ink-soft">{t('address')}</dt>
                  <dd className="mt-1 font-medium text-ink">{result.data.address || '—'}</dd>
                </div>
                <div>
                  <dt className="text-sm text-ink-soft">{t('location')}</dt>
                  <dd className="mt-1 font-medium text-ink">{result.data.location || '—'}</dd>
                </div>
                <div>
                  <dt className="text-sm text-ink-soft">{t('approval')}</dt>
                  <dd className="mt-1 font-medium text-ink">
                    {result.data.admin_approved ? t('approved') : t('pending')}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-ink-soft">{t('visibility')}</dt>
                  <dd className="mt-1 font-medium text-ink">
                    {result.data.marketing_enabled ? t('visible') : t('hidden')}
                  </dd>
                </div>
              </dl>
            </Card>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link
                href={`/${locale}/market`}
                className="rounded-md bg-forest px-4 py-2 text-sm font-semibold text-paper"
              >
                {t('browseProducts')}
              </Link>
              <Link
                href={`/${locale}/market/bazaars`}
                className="rounded-md border border-line px-4 py-2 text-sm font-semibold text-ink"
              >
                {t('allBazaars')}
              </Link>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
