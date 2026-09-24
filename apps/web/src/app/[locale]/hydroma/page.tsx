import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { SiteNav } from '@/components/SiteNav';
import { routing } from '@/i18n/routing';
import { apiGet, type CppStatus } from '@/lib/api/client';
import { loadMessages } from '@/lib/i18n/messages';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

// Type for nested messages structure
type NestedMessages = {
  brand?: { name?: string };
  science?: { lead?: string };
};

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const messages = (await loadMessages(locale)) as NestedMessages;
  const brandName = messages.brand?.name ?? 'هیدروما نوژین';
  const scienceLead = messages.science?.lead ?? 'موتور علمی و ابزارهای هیدروما';

  return {
    title: `علم · ${brandName}`,
    description: scienceLead,
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/hydroma`,
      title: `علم · ${brandName}`,
      description: scienceLead,
      images: [
        { url: `${BASE_URL}/og-science.png`, width: 1200, height: 630, alt: 'Eco Nojin Science' },
      ],
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/hydroma`,
      languages: Object.fromEntries(
        routing.locales.map((loc) => [loc, `${BASE_URL}/${loc}/hydroma`]),
      ),
    },
  };
}

export const dynamic = 'force-dynamic';

export default async function HydromaPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const cpp = await apiGet<CppStatus>('/api/v1/models/cpp-status');
  const available = cpp.ok && cpp.data.available;

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <h1 className="display text-4xl font-bold text-ink">{t('science.title')}</h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('science.lead')}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 py-2">
        <div
          className={available ? 'card p-4 text-sm text-forest' : 'card p-4 text-sm text-copper'}
        >
          <strong>{available ? t('science.cppOk') : t('science.cppMissing')}</strong>
          <p className="mt-2 text-xs text-ink-soft">{t('science.modelsPublicNote')}</p>
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-6 py-6 pb-16">
        <h2 className="text-sm font-semibold text-ink-soft">{t('science.modelsTitle')}</h2>
        <p className="mt-3 text-xs text-ink-soft">{t('science.modelsPublicNote')}</p>
      </section>
    </main>
  );
}