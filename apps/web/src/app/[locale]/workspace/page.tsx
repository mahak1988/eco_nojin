import { redirect } from 'next/navigation';
import { setRequestLocale } from 'next-intl/server';
import { getWorkspacePage } from '@/lib/workspaces/registry';

/**
 * The workspace root is not a page of its own: the design document registers
 * `overview` as the workspace index, so the root resolves to it instead of
 * inventing an extra surface that has no contract of its own.
 */
export default async function WorkspaceIndexPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  redirect(`/${locale}/workspace/${getWorkspacePage('overview').path}`);
}
