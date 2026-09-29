import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { type FamilyKey, ToolFamilyPage } from '../_lib/family';
import { hydromaMetadata } from '../_lib/metadata';

/**
 * The soil tool family.
 *
 * Contract: `GET /api/v1/hydroma/soil` — `hydroma_soil.py:425-428`, which returns
 * `{"count": len(_SPECS), "models": _SPECS}`, so the rows key is `models`.
 * Nine tools are declared: the USDA texture triangle, Keys to Soil Taxonomy, the
 * van Genuchten retention curve, Saxton & Rawls pedotransfer, Brooks-Corey and
 * Campbell physics, Brady & Weil chemistry, FAO-29 salinity, and two USDA NRCS
 * 2023 fertility tools.
 */
const FAMILY: FamilyKey = 'soil';
const ROUTE = '/hydroma/soil';

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
