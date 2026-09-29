import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { hydromaMetadata } from '../../_lib/metadata';
import { ReferenceDataPage } from '../../_lib/suite';

/**
 * The published reference values the verification suite is meant to be judged
 * against.
 *
 * Contract: `GET /api/v1/hydroma/validation/reference-data` —
 * `services/validation/router.py:47-58`, which reads
 * `docs/hydroma/scientific_reference_data.json` and returns
 * `{"error": "Reference data file not found"}` when it is absent.
 *
 * **That file is not in the repository.** The contract therefore cannot answer with
 * reference values today, and the page reports the contract's own error rather than
 * substituting the `source` strings from `formula_checks` and calling them reference
 * data. The same absence means `formula_checks._reference_data()` returns `{}` on
 * every run.
 */
const ROUTE = '/hydroma/validation/reference-data';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('hydroma.pages.suiteReference');
  return hydromaMetadata({
    locale,
    route: ROUTE,
    title: meta('title'),
    description: meta('description'),
  });
}

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  return <ReferenceDataPage locale={locale} />;
}
