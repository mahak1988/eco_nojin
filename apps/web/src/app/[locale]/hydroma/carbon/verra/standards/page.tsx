import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { fetchResource, ResourcePage, resourceLabels } from '@/components/ResourcePage';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';

const SLUG = 'hydroma-hydroma-carbon-verra-standards';
const ROUTE = '/hydroma/carbon/verra/standards';
/** The declared contract. A dynamic segment is resolved from the route params. */
const PATH = '/api/v1/carbon/verra/standards';

/**
 * Generated from the page catalogue — do not hand-edit.
 *
 * Entry `hydroma-hydroma-carbon-verra-standards`, domain `hydroma`. Source of truth: `services/api_gateway/routers/carbon.py`.
 * The endpoint is the declared contract; the page renders one of the five
 * required states and never a fabricated value.
 */
type Payload = Record<string, unknown>;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.hydroma-hydroma-carbon-verra-standards');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}${ROUTE}`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, ROUTE),
      languages: languageAlternates(ROUTE),
    },
  };
}

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.hydroma-hydroma-carbon-verra-standards');
  const labels = await resourceLabels();
  const endpoint = PATH;

  const result = await fetchResource<Payload>(endpoint);

  return (
    <ResourcePage<Payload>
      slug={SLUG}
      locale={locale}
      title={meta('title')}
      description={meta('description')}
      path={endpoint}
      result={result}
      mode="rows"
      rowsKey={'standards'}
      rowKey={(row) => String(row.id ?? JSON.stringify(row).slice(0, 24))}
      labels={labels}
    ></ResourcePage>
  );
}
