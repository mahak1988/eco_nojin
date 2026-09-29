import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { BazaarStepRenderer } from '@/components/market/BazaarStepRenderer';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.template');

  return {
    title: t('title'),
    description: t('description'),
    robots: { index: false, follow: true },
  };
}

/**
 * Step 5 of the establishment flow, rendered by `BazaarStepRenderer`.
 *
 * The step stays unavailable: no gateway endpoint exists for it, so the renderer
 * reports its real state rather than collecting input that cannot be persisted.
 */
export default async function BazaarWizardStep5Page({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale } = await params;
  return (
    <main id="main-content" className="min-h-dvh">
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <BazaarStepRenderer step={5} locale={locale} />
      </div>
    </main>
  );
}
