import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { type FamilyKey, ToolFamilyPage } from '../_lib/family';
import { hydromaMetadata } from '../_lib/metadata';

/**
 * The index family.
 *
 * Contract: `GET /api/v1/hydroma/indices` — `hydroma_indices.py:566-569`, which
 * returns `{"count": len(_SPECS), "models": _SPECS}`, so the rows key is `models`.
 * Eight indices are declared, and their `reference` strings carry the
 * methodological limits the page must not hide: ECSI's own reference says moisture
 * is a rainfall/evaporation proxy and that `rothc_runner` should be used when soil
 * moisture deficit is available.
 */
const FAMILY: FamilyKey = 'indices';
const ROUTE = '/hydroma/indices';

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
