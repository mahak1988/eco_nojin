import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { UnavailableCapability } from '../../data-states';

// Only a per-case lookup is registered, and it needs a dispute id a visitor does
// not have; the listing itself is authenticated, so no case is rendered here.
const CASE_PATH = '/api/v1/disputes/{dispute_id}';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.public-components-dispute-resolution');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/components/dispute-resolution`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/public/components/dispute-resolution'),
      languages: languageAlternates('/public/components/dispute-resolution'),
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

  const meta = await getTranslations('pageMeta.public-components-dispute-resolution');
  const common = await getTranslations('common');
  const title = meta('title');
  const description = meta('description');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
          <ProvenanceStamp source={CASE_PATH} label={title} verified={false} method={CASE_PATH} />
        </div>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <UnavailableCapability path={CASE_PATH} />
        <p className="mt-6 text-xs text-ink-soft">{common('limits')}</p>
      </section>
    </main>
  );
}
