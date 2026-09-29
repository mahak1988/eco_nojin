import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { UnavailableCapability } from '../../data-states';

const SLUGS_PATH = '/api/v1/legal-texts/slugs';
const TEXT_PATH = '/api/v1/legal-texts/{locale}/governance';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.public-policy-governance');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/policy/governance`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/public/policy/governance'),
      languages: languageAlternates('/public/policy/governance'),
    },
  };
}

export default async function GovernancePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  const meta = await getTranslations('pageMeta.public-policy-governance');
  const common = await getTranslations('common');
  const title = meta('title');
  const description = meta('description');
  const missing = TEXT_PATH.replace('{locale}', locale).replace('{slug}', 'governance');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="display text-4xl font-bold text-ink">{title}</h1>
          <ProvenanceStamp source={missing} label={title} verified={false} method={missing} />
        </div>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
        <div className="mt-6">
          <UnavailableCapability path={missing} />
        </div>
        <p className="mt-6 text-xs text-ink-soft">
          {common('limits')} · {SLUGS_PATH}
        </p>
      </div>
    </main>
  );
}
