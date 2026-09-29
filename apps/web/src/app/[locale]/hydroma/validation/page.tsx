import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { hydromaMetadata } from '../_lib/metadata';
import { SuitePage } from '../_lib/suite';

/**
 * The formula-verification suite — the transparency surface of the whole engine.
 *
 * Contract: `GET /api/v1/hydroma/validation` — `hydroma_ops.py:20-27`, which
 * returns `run_all()` from `services/validation/formula_checks.py`. The envelope is
 * `{total, passed, failed, pass_rate, checks}`, so the rows key is `checks` and
 * every check carries `source` (the cited publication it is judged against),
 * `expected`, `actual` and `tolerance`.
 */
const ROUTE = '/hydroma/validation';

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('hydroma.pages.suite');
  return hydromaMetadata({
    locale,
    route: ROUTE,
    title: meta('title'),
    description: meta('description'),
  });
}

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  return <SuitePage locale={locale} />;
}
