import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { type FamilyKey, ToolSpecPage } from '../../_lib/family';
import { hydromaMetadata } from '../../_lib/metadata';

/**
 * One index: its parameter contract, its record, and what it does not publish.
 *
 * Contract: `GET /api/v1/hydroma/indices/{model_id}` â€” `hydroma_indices.py:572-577`,
 * `return spec`, with a 404 naming the registry for an undeclared id.
 */
const FAMILY: FamilyKey = 'indices';
export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; model_id: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations(`hydroma.families.${FAMILY}`);
  return hydromaMetadata({
    locale,
    route: '/hydroma/indices',
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
