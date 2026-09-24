import { getTranslations } from 'next-intl/server';

export async function OwnerFooter() {
  const t = await getTranslations();
  return (
    <footer className="mt-10 border-t border-line">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-6 px-6 py-8">
        <div className="flex flex-wrap items-center gap-4">
          <img
            src="/brand/owner-narvan-logo.png"
            alt={t('owner.logoAlt')}
            className="h-14 w-auto"
          />
          <span className="text-xs text-ink-soft">{t('owner.line')}</span>
        </div>
        <img
          src="/brand/platform-logo.webp"
          alt={t('brand.logoAlt')}
          className="h-8 w-auto opacity-70"
        />
      </div>
    </footer>
  );
}
