import { getTranslations } from 'next-intl/server';

/**
 * Workspace loading state. It states that the surface is being resolved rather
 * than showing a spinner, a count or any record that no backend has returned.
 */
export default async function WorkspaceLoading() {
  const t = await getTranslations();

  return (
    <div className="card p-5" role="status" aria-live="polite">
      <p className="text-sm font-semibold text-ink">{t('auth.session.loading')}</p>
      <p className="mt-2 text-sm text-ink-soft">{t('statusPage.subtitle')}</p>
    </div>
  );
}
