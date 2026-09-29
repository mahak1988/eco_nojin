import { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { Card } from '@/components/ui/Card';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';
import { UnavailableCapability } from '../../data-states';

// The LMS video routes are not registered on the gateway, so no asset is served.
const MISSING_PATH = '/api/v1/public/education/video';
const SEARCH_PATH = '/api/v1/content/search';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.public-education-video-player');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/public/education/video-player`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/public/education/video-player'),
      languages: languageAlternates('/public/education/video-player'),
    },
  };
}

export default async function VideoPlayerPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  const meta = await getTranslations('pageMeta.public-education-video-player');
  const learn = await getTranslations('learn');
  const common = await getTranslations('common');
  const title = meta('title');
  const description = meta('description');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp
          source={MISSING_PATH}
          label={title}
          verified={false}
          method={MISSING_PATH}
        />
        <h1 className="display text-4xl font-bold text-ink">{title}</h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{description}</p>
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-6">
        <UnavailableCapability path={MISSING_PATH} contract={false} />
      </section>

      <section className="mx-auto max-w-5xl px-6 pb-12">
        <h2 className="text-xl font-semibold text-ink mb-4">{SEARCH_PATH}</h2>
        <Card density="compact">
          <h3 className="text-sm font-medium text-ink">{learn('emptyTitle')}</h3>
          <p className="mt-1 text-sm text-ink-soft">{learn('emptyDesc')}</p>
          <Link
            href={`/${locale}/public/education/library`}
            className="mt-3 inline-flex text-sm font-semibold text-[var(--color-forest)]"
          >
            {common('view')}
          </Link>
        </Card>
      </section>
    </main>
  );
}
