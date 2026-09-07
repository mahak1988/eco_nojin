import { useTranslation } from 'react-i18next';
import { Link } from '@tanstack/react-router';
import { Badge, Reveal } from '@eco/ui';
import { DASHBOARD_URL } from '@eco/config';

export function CallToAction() {
  const { t } = useTranslation();
  return (
    <section className="py-24 lg:py-32">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <Reveal>
          <div className="relative overflow-hidden rounded-3xl bg-ink px-8 py-16 text-center text-ink-inverse shadow-elevated sm:px-12 lg:py-20">
            <div
              aria-hidden
              className="absolute inset-0 opacity-25"
              style={{
                backgroundImage:
                  'radial-gradient(circle at 15% 20%, rgb(var(--color-brand-400)) 0%, transparent 40%), radial-gradient(circle at 80% 80%, rgb(var(--color-sky-400)) 0%, transparent 45%)',
              }}
            />
            <div className="relative">
              <Badge tone="brand" variant="solid" className="mx-auto mb-6">{t('cta.badge')}</Badge>
              <h2 className="mx-auto max-w-2xl text-balance text-4xl font-bold tracking-tight sm:text-5xl">{t('cta.title')}</h2>
              <p className="mx-auto mt-5 max-w-2xl text-balance text-base leading-relaxed text-ink-inverse/80 md:text-lg">{t('cta.body')}</p>
              <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
                <a
                  href={DASHBOARD_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex h-12 items-center gap-2 rounded-full bg-white px-7 text-sm font-semibold text-ink shadow-raised transition-all hover:-translate-y-0.5 hover:shadow-elevated"
                >
                  {t('home.openDashboard')}
                  <span aria-hidden className="rtl-flip">→</span>
                </a>
                <Link
                  to="/knowledge"
                  className="inline-flex h-12 items-center gap-2 rounded-full border border-ink-inverse/20 bg-ink-inverse/5 px-7 text-sm font-semibold text-ink-inverse transition-colors hover:bg-ink-inverse/10"
                >
                  {t('cta.secondary')}
                </Link>
              </div>
              <p className="mt-8 text-xs text-ink-inverse/50">{t('cta.footer')}</p>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
