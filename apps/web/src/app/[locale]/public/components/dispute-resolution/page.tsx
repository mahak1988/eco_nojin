import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { SITE_URL as BASE_URL } from '@/config/site';
import { UnavailableCapability } from '../../data-states';

// Only a per-case lookup is registered, and it needs a dispute id a visitor does
// not have; the listing itself is authenticated, so no case is rendered here.
const CASE_PATH = '/api/v1/disputes/{dispute_id}';

const TITLES: Record<string, string> = {
  fa: 'نمایشگاه حل اختلاف',
  en: 'Dispute Resolution Demo',
};
const DESCRIPTIONS: Record<string, string> = {
  fa: 'فهرست پرونده‌های اختلاف در گیتوی ثبت نشده است؛ هیچ پرونده یا رأیی نمایش داده نمی‌شود',
  en: 'No dispute listing is registered on the gateway; no case or verdict is shown',
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
      url: `${BASE_URL}/${locale}/public/components/dispute-resolution`,
      title: TITLES[locale] ?? TITLES.en,
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/public/components/dispute-resolution`,
      languages: {
        fa: `${BASE_URL}/fa/public/components/dispute-resolution`,
        en: `${BASE_URL}/en/public/components/dispute-resolution`,
      },
    },
  };
}

export default async function DisputeResolutionPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const common = await getTranslations('common');
  const title = TITLES[locale] ?? TITLES.en;
  const description = DESCRIPTIONS[locale] ?? DESCRIPTIONS.en;

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source={CASE_PATH} label={title} verified={false} method={CASE_PATH}>
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <UnavailableCapability path={CASE_PATH} />
        <p className="mt-6 text-xs text-ink-soft">{common('limits')}</p>
      </section>
    </main>
  );
}
