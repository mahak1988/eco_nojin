import type { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { StatusDot } from '@/components/StatusDot';
import { Card } from '@/components/ui/Card';

interface MarketplaceTemplatePageProps {
  locale: string;
  group: string;
  slug: string;
}

export async function generateMarketplaceMetadata({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}): Promise<Metadata> {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.template');

  return {
    title: `${t('title')} · ${slug}`,
    description: t('description'),
    robots: { index: false, follow: true },
  };
}

export async function MarketplaceTemplatePage({
  locale,
  group,
  slug,
}: MarketplaceTemplatePageProps) {
  setRequestLocale(locale);
  const t = await getTranslations('market.template');

  return (
    <main id="main-content" className="min-h-dvh">
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <Link href={`/${locale}/market`} className="text-sm text-[var(--color-forest)]">
          {t('back')}
        </Link>
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <StatusDot state="warn" label={t('status')} />
          <span className="font-mono text-xs text-ink-soft">
            {group}/{slug}
          </span>
        </div>
        <ProvenanceStamp
          source={t('source')}
          label={t('source')}
          verified={false}
          method={t('method')}
        />
        <Card density="cozy" className="mt-6">
          <h1 className="display text-3xl font-bold text-ink">{t('title')}</h1>
          <p className="mt-3 text-ink-soft">{t('description')}</p>
          <div className="mt-6 rounded-md border border-line bg-surface-alt p-4">
            <h2 className="font-semibold text-ink">{t('unavailableTitle')}</h2>
            <p className="mt-2 text-sm text-ink-soft">{t('unavailableDescription')}</p>
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
