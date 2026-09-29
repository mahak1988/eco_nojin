import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { type FamilyKey, ToolSpecPage } from '../../_lib/family';
import { hydromaMetadata } from '../../_lib/metadata';

/**
 * One water tool: its parameter contract, its record, and what it does not publish.
 *
 * Contract: `GET /api/v1/hydroma/water/{model_id}` â€” `hydroma_water.py:269-274`,
 * `return spec`, with a 404 naming the registry for an undeclared id.
 */
const FAMILY: FamilyKey = 'water';
export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; model_id: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations(`hydroma.families.${FAMILY}`);
  return hydromaMetadata({
    locale,
    route: '/hydroma/water',
    title: meta('toolTitle'),
    description: meta('toolDescription'),
  });
}

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; model_id: string }>;
}) {
  const { locale, model_id: modelId } = await params;
  return <ToolSpecPage locale={locale} family={FAMILY} modelId={modelId} />;
}
