import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { hydromaMetadata } from '../../_lib/metadata';
import { ModelDetailPage } from '../../_lib/registry';

/**
 * One model's registry record.
 *
 * Contract: `GET /api/v1/hydroma/models/{model_id}` â€” `hydroma_dashboard.py:737-749`,
 * `return ModelDetail(**model_data)`, with a 404 naming the model when the id is not
 * in `_discover_models()`.
 *
 * The record is the only response in this subtree that publishes a version, so the
 * transparency bar is genuinely populated here â€” and genuinely empty in two slots,
 * because `_discover_models` never sets `inputs`, `outputs` or `performance`.
 */
export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; model_id: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('hydroma.pages.model');
  return hydromaMetadata({
    locale,
    route: '/hydroma/models',
    title: meta('title'),
    description: meta('description'),
  });
}

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; model_id: string }>;
}) {
  const { locale, model_id: modelId } = await params;
  return <ModelDetailPage locale={locale} modelId={modelId} />;
}
