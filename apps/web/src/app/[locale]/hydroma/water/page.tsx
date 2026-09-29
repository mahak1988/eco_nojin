import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { type FamilyKey, ToolFamilyPage } from '../_lib/family';
import { hydromaMetadata } from '../_lib/metadata';

/**
 * The water tool family.
 *
 * Contract: `GET /api/v1/hydroma/water` — `hydroma_water.py:263-266`, which returns
 * `{"count": len(_SPECS), "models": _SPECS}`, so the rows key is `models`.
 * Four tools are declared: SCS-CN and rational-method runoff, and the
 * groundwater model and its confined/unconfined service, both on Todd & Mays 2005.
 */
const FAMILY: FamilyKey = 'water';
const ROUTE = '/hydroma/water';

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
