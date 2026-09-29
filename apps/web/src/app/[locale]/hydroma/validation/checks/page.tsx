import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { hydromaMetadata } from '../../_lib/metadata';
import { SuiteChecksPage } from '../../_lib/suite';

/**
 * The catalogue of verification checks.
 *
 * Contract: `GET /api/v1/hydroma/validation/checks` — `services/validation/router.py:32-44`,
 * which returns `{"checks": [{"id", "label", "kind", "unit"}], "total"}`. The rows
 * key is `checks`; the envelope is not pluralised from the leaf.
 *
 * The projection is narrower than the report's: it drops `source`, `expected`,
 * `actual` and `tolerance`, so the transparency bar has nothing to read here and
 * says so rather than borrowing the report's values.
 */
const ROUTE = '/hydroma/validation/checks';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('hydroma.pages.suiteChecks');
  return hydromaMetadata({
    locale,
    route: ROUTE,
    title: meta('title'),
    description: meta('description'),
  });
}

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  return <SuiteChecksPage locale={locale} />;
}
