import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { hydromaMetadata } from '../../../_lib/metadata';
import { ModelValidationPage } from '../../../_lib/registry';

/**
 * One model's validation report â€” and the page that must not overstate it.
 *
 * Contract: `GET /api/v1/hydroma/models/{model_id}/validation` â€”
 * `hydroma_dashboard.py:752-800`.
 *
 * The handler is explicit in its own comments (`:763-764`): *"In a real
 * implementation, this would run the actual tests / For now, return mock report
 * based on test case definitions."* A fixture with an `expected` key is marked
 * `passed` without anything executing, `failed` is always `0`, and
 * `overall_status` is `"passed"` whenever that zero holds. The page therefore shows
 * a **declared, not executed** badge, and `verified` is pinned to `false` on the
 * provenance stamp even on a 200 â€” the plan's rule is that a simulated value says
 * so even when the caller declared it real.
 */
export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; model_id: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('hydroma.pages.modelValidation');
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
  return <ModelValidationPage locale={locale} modelId={modelId} />;
}
