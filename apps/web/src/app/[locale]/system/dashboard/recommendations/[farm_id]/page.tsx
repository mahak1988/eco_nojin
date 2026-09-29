import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { fetchResource, ResourcePage, resourceLabels } from '@/components/ResourcePage';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';

const SLUG = 'system-system-dashboard-recommendations-farm_id';
const ROUTE = '/system/dashboard/recommendations/{farm_id}';
/** The declared contract. A dynamic segment is resolved from the route params. */
const PATH = '/dashboard/recommendations/{farm_id}';

/**
 * Generated from the page catalogue — do not hand-edit.
 *
 * Entry `system-system-dashboard-recommendations`, domain `system`. Source of truth: `services/api_gateway/routers/dashboard.py`.
 * The endpoint is the declared contract; the page renders one of the five
 * required states and never a fabricated value.
 */
type Payload = Record<string, unknown>;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; farm_id: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('pageMeta.system-system-dashboard-recommendations-farm_id');
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}${ROUTE.replace(/\{[a-z_]+\}/g, '·')}`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, ROUTE),
      languages: languageAlternates(ROUTE),
    },
  };
}

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; farm_id: string }>;
}) {
  const { locale, ...rest } = await params;
  const meta = await getTranslations('pageMeta.system-system-dashboard-recommendations-farm_id');
  const labels = await resourceLabels();
  // A dynamic segment is resolved from the route params rather than requested
  // as a literal template. "rest" is used instead of a second "params" binding,
  // which collided with the destructured parameter and failed to compile.
  const routeParams = rest as Record<string, string>;
  const endpoint = String(PATH).replace(/\{(\w+)\}/g, (_m, key) => String(routeParams[key] ?? ''));
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
      rowsKey={'{farm_id}s'}
      rowKey={(row) => String(row.id ?? JSON.stringify(row).slice(0, 24))}
      labels={labels}
    ></ResourcePage>
  );
}
