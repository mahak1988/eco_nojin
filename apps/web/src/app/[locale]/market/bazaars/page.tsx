import type { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';
import { BAZAARS_SOURCE, listBazaars } from '@/lib/api/market';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.bazaar');
  return {
    title: t('title'),
    description: t('lead'),
    robots: { index: true, follow: true },
  };
}

export default async function BazaarsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.bazaar');
  const common = await getTranslations('common');
  const statusLine = await getTranslations('statusLine');
  const result = await listBazaars();
  const bazaars = result.ok ? result.data : [];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-5xl px-6 pb-12 pt-8">
        <header className="mb-8 flex flex-wrap items-start gap-4">
          <div className="flex-1">
            <h1 className="display text-balance text-4xl font-bold text-ink">{t('title')}</h1>
            <p className="mt-3 text-ink-soft">{t('lead')}</p>
          </div>
          <Link
            href={`/${locale}/market/bazaars/create`}
            className="rounded-md bg-action px-4 py-2 text-sm font-semibold text-on-action"
          >
            {t('create')}
          </Link>
        </header>

        <ProvenanceStamp
          source={BAZAARS_SOURCE}
          label={t('source')}
          method={result.ok ? statusLine('realData') : statusLine('unavailable')}
        />

        {!result.ok ? (
          <Card density="cozy" className="mt-6">
            <p className="text-sm text-clay">{result.error}</p>
          </Card>
        ) : bazaars.length === 0 ? (
          <Card density="cozy" className="mt-6">
            <p className="text-sm text-ink-soft">{t('empty')}</p>
          </Card>
        ) : (
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            {bazaars.map((bazaar) => (
              <Card key={bazaar.id} density="cozy">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold text-ink">{bazaar.name}</h2>
                    <p className="mt-1 text-sm text-ink-soft">{bazaar.description}</p>
                  </div>
                  <StatusDot
                    state={bazaar.status === 'approved' ? 'ok' : 'warn'}
                    label={bazaar.status}
                  />
                </div>
                <dl className="mt-4 space-y-2 text-sm">
                  <div className="flex justify-between gap-3">
                    <dt className="text-ink-soft">{t('type')}</dt>
                    <dd className="text-end text-ink">{bazaar.marketplace_type}</dd>
                  </div>
                  <div className="flex justify-between gap-3">
                    <dt className="text-ink-soft">{t('address')}</dt>
                    <dd className="text-end text-ink">{bazaar.address || '—'}</dd>
                  </div>
                </dl>
                <Link
                  href={`/${locale}/market/bazaars/${bazaar.id}`}
                  className="mt-4 inline-block text-sm font-semibold text-forest underline"
                >
                  {common('view')}
                </Link>
              </Card>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
