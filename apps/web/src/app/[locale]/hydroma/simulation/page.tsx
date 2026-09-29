import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { type FamilyKey, ToolFamilyPage } from '../_lib/family';
import { hydromaMetadata } from '../_lib/metadata';

/**
 * The simulation family.
 *
 * Contract: `GET /api/v1/hydroma/simulation` — `hydroma_simulation.py:83-86`, which
 * returns `{"count": len(_SPECS), "models": _SPECS}`, so the rows key is `models`.
 * Two tools are declared: Sobol calibration after Saltelli 2010, and the scenario
 * matrices of HyDroMa document 28. `sim-scenarios` declares no parameters at all,
 * which the input panel states rather than hiding behind an empty list.
 */
const FAMILY: FamilyKey = 'simulation';
const ROUTE = '/hydroma/simulation';

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
