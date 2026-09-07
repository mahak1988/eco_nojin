import { useTranslation } from 'react-i18next';
import { Link } from '@tanstack/react-router';
import { DASHBOARD_URL } from '@eco/config';

export function CallToAction() {
  const { t } = useTranslation();
  return (
    <section className="bg-surface-muted py-28">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-balance text-4xl font-bold tracking-tight text-ink sm:text-5xl">{t('cta.title')}</h2>
          <p className="mx-auto mt-5 max-w-xl text-balance text-base leading-relaxed text-ink-muted md:text-lg">{t('cta.body')}</p>
          <div className="mt-9 flex flex-wrap items-center justify-center gap-6">
            <a
              href={DASHBOARD_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex h-12 items-center rounded-full bg-gradient-brand px-7 text-sm font-medium text-white transition-all hover:opacity-90 focus-visible:outline-none"
            >
              {t('home.openDashboard')}
            </a>
            <Link to="/knowledge" className="link-apple inline-flex items-center gap-1 text-base">
              {t('cta.secondary')}
              <span aria-hidden className="rtl-flip">‹</span>
            </Link>
          </div>
          <p className="mt-8 text-xs text-ink-subtle">{t('cta.footer')}</p>
        </div>
      </div>
    </section>
  );
}
