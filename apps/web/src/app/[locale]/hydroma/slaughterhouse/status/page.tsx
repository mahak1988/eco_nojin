import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { hydromaMetadata } from '../../_lib/metadata';
import { SlaughterhousePage } from '../../_lib/registry';

/**
 * The validation roll-up across the whole registry.
 *
 * Contract: `GET /api/v1/hydroma/slaughterhouse/status` —
 * `hydroma_dashboard.py:832-861`, `response_model=SlaughterhouseStatus`. Six
 * counters, `last_run`, and `recent_failures`.
 *
 * The counters tally the registry's own declared `status` field, so they describe
 * declarations; `last_run` is the moment the read was served. Both are stated on
 * the page rather than presented as an executed validation pass.
 */
const ROUTE = '/hydroma/slaughterhouse/status';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('hydroma.pages.slaughterhouse');
  return hydromaMetadata({
    locale,
    route: ROUTE,
    title: meta('title'),
    description: meta('description'),
  });
}

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  return <SlaughterhousePage locale={locale} />;
}
