import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { hydromaMetadata } from '../../_lib/metadata';
import { RunCheckPage } from '../../_lib/suite';

/**
 * Run one verification check.
 *
 * Contract: `GET /api/v1/hydroma/validation/run` — `services/validation/router.py:8-29`.
 * `check_id` is optional: absent returns the whole suite, present returns the one
 * matching check, and present-but-unknown returns `{"error": "Check '…' not found"}`
 * with HTTP **200**. A 200 carrying a failure is why this page reads `error` out of
 * the body and reports it, rather than reporting a clean run.
 *
 * This is the one surface in the validation family with a real parameter, so its
 * input panel is that parameter — a no-JS form that re-navigates to this URL with
 * `?check_id=…`.
 */
const ROUTE = '/hydroma/validation/run';

export const dynamic = 'force-dynamic';

function first(value: string | string[] | undefined): string {
  return (Array.isArray(value) ? value[0] : value) ?? '';
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations('hydroma.pages.suiteRun');
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
  return <RunCheckPage locale={locale} checkId={first(query?.check_id)} />;
}
