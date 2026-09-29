import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { type FamilyKey, ToolSpecPage } from '../../_lib/family';
import { hydromaMetadata } from '../../_lib/metadata';

/**
 * One soil tool: its parameter contract, its record, and what it does not publish.
 *
 * Contract: `GET /api/v1/hydroma/soil/{model_id}` â€” `hydroma_soil.py:431-436`,
 * `return spec`, and a 404 with `detail: "unknown HyDroMa soil tool: â€¦"` for an id
 * the registry does not declare. That 404 is a real answer, so the page reports it
 * as an error state naming the contract rather than rendering an empty record.
 */
const FAMILY: FamilyKey = 'soil';
export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; model_id: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations(`hydroma.families.${FAMILY}`);
  return hydromaMetadata({
    locale,
    route: '/hydroma/soil',
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
