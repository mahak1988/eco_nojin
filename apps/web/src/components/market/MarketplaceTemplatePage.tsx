import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';

interface MarketplaceTemplatePageProps {
  locale: string;
  group: string;
  slug: string;
  /** Real gateway path this route would read, when one already exists. */
  source?: string;
}

/**
 * Shared state for marketplace routes whose data source is not connected yet.
 * It reports the route, never a stand-in payload, so an unavailable capability
 * can never be mistaken for live data.
 */
export async function MarketplaceTemplatePage({
  locale,
  group,
  slug,
  source,
}: MarketplaceTemplatePageProps) {
  setRequestLocale(locale);
  const t = await getTranslations('market.template');
  const statusLine = await getTranslations('statusLine');
  const route = `${group}/${slug}`;

  return (
    <main id="main-content" className="min-h-dvh">
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <Link href={`/${locale}/market`} className="text-sm text-[var(--color-forest)]">
          {t('back')}
        </Link>
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <StatusDot state="warn" label={t('status')} />
          <span className="font-mono text-xs text-ink-soft">{route}</span>
          <ProvenanceStamp source={source ?? route} label={t('source')} />
        </div>
        <Card density="cozy" className="mt-6">
          <h1 className="display text-3xl font-bold text-ink">{t('title')}</h1>
          <p className="mt-3 text-ink-soft">{t('description')}</p>
          <div className="mt-6 rounded-md border border-line p-4">
            <h2 className="font-semibold text-ink">{t('unavailableTitle')}</h2>
            <p className="mt-2 text-sm text-ink-soft">{t('unavailableDescription')}</p>
            <p role="status" className="mt-2 text-sm text-ink-soft">
              {statusLine('unavailable')}
            </p>
          </div>
          <div className="mt-6 grid gap-3 md:grid-cols-2">
            <div className="rounded-md border border-line p-4">
              <h3 className="font-medium text-ink">{t('contractTitle')}</h3>
              <p className="mt-1 text-sm text-ink-soft">{t('contractDescription')}</p>
            </div>
            <div className="rounded-md border border-line p-4">
              <h3 className="font-medium text-ink">{t('nextTitle')}</h3>
              <p className="mt-1 text-sm text-ink-soft">{t('nextDescription')}</p>
            </div>
          </div>
        </Card>
      </div>
    </main>
  );
}
