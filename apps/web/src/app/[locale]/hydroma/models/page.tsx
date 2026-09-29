import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { hydromaMetadata } from '../_lib/metadata';
import { ModelListPage } from '../_lib/registry';

/**
 * The HyDroMa model registry.
 *
 * Contract: `GET /api/v1/hydroma/models` — `hydroma_dashboard.py:714-734`,
 * `return [ModelMeta(**m) for m in models]`. The payload **is** the array, so
 * there is no envelope key: `readRows` is called without one, which is the case
 * that produced `{error_id}s` on a sibling surface when the key was guessed.
 *
 * `category`, `status` and `language` are the endpoint's own query parameters
 * (`:716-718`), and the page's input panel is a no-JS form over exactly those
 * three — so the control is the contract, not a decoration beside it.
 */
const ROUTE = '/hydroma/models';

function first(value: string | string[] | undefined): string {
  return (Array.isArray(value) ? value[0] : value) ?? '';
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('hydroma.pages.models');
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
  const query = await searchParams;
  return (
    <ModelListPage
      locale={locale}
      category={first(query?.category)}
      status={first(query?.status)}
      language={first(query?.language)}
    />
  );
}
