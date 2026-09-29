import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { type FamilyKey, ToolFamilyPage } from '../_lib/family';
import { hydromaMetadata } from '../_lib/metadata';

/**
 * The MRV family — monitoring, reporting and verification.
 *
 * Contract: `GET /api/v1/hydroma/mrv` — `hydroma_mrv.py:139-141`, which returns
 * `{"count": len(_SPECS), "models": _SPECS}`, so the rows key is `models`.
 * Two tools are declared, both on the EM-01 method: `mrv-qa` (the QA bands) and
 * `mrv-metrics` (§3, which is where the `real / simulated / no_data` distinction
 * the plan's simulation-tint rule comes from is written down).
 */
const FAMILY: FamilyKey = 'mrv';
const ROUTE = '/hydroma/mrv';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations(`hydroma.families.${FAMILY}`);
  return hydromaMetadata({
    locale,
    route: ROUTE,
    title: meta('title'),
    description: meta('description'),
  });
}

export default async function Page({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { locale } = await params;
  const resolved = await searchParams;
  const raw = resolved?.q;
  const term = (Array.isArray(raw) ? raw[0] : raw) ?? '';
  return <ToolFamilyPage locale={locale} family={FAMILY} term={term} />;
}
