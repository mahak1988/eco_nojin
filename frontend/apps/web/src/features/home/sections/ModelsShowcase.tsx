import { useTranslation } from 'react-i18next';
import { Badge } from '@eco/ui';
import { Reveal } from '@eco/ui';
import { DASHBOARD_URL } from '@eco/config';
import { cn } from '@eco/utils';
import { roleClasses } from '@eco/ui/tokens';

/* ================================================================
   DATA
   ================================================================ */
export const MODELS = [
  {
    id: 'swat',
    domain: 'water',
    domainKey: 'models.domains.water',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z" strokeLinejoin="round" />
      </svg>
    ),
    gradient: 'from-sky-500 to-cyan-600',
    soft: 'bg-sky-50 dark:bg-sky-950/40',
    badge: 'bg-sky-100 text-sky-700 dark:bg-sky-900 dark:text-sky-200',
  },
  {
    id: 'pywr',
    domain: 'water',
    domainKey: 'models.domains.water',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <circle cx="6" cy="6" r="3" /><circle cx="18" cy="6" r="3" /><circle cx="12" cy="18" r="3" />
        <path d="M8.5 7.5L10.5 16.5M15.5 7.5L13.5 16.5M6 9h12" strokeLinejoin="round" />
      </svg>
    ),
    gradient: 'from-teal-500 to-emerald-600',
    soft: 'bg-teal-50 dark:bg-teal-950/40',
    badge: 'bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-200',
  },
  {
    id: 'hecras',
    domain: 'hydraulic',
    domainKey: 'models.domains.hydraulic',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M3 12h4l3-9 4 18 3-9h4" strokeLinejoin="round" strokeLinecap="round" />
      </svg>
    ),
    gradient: 'from-indigo-500 to-blue-700',
    soft: 'bg-indigo-50 dark:bg-indigo-950/40',
    badge: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-200',
  },
  {
    id: 'aquacrop',
    domain: 'crop',
    domainKey: 'models.domains.crop',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M12 22V12" strokeLinecap="round" />
        <path d="M12 12c-2-4-6-5-6-5s3 2 6-2c3 4 6 2 6 2s-4-1-6-5z" strokeLinejoin="round" />
        <path d="M12 16c1.5-3 4.5-4 4.5-4s-2 1-4.5-2z" strokeLinejoin="round" opacity="0.5" />
      </svg>
    ),
    gradient: 'from-lime-500 to-green-700',
    soft: 'bg-lime-50 dark:bg-lime-950/40',
    badge: 'bg-lime-100 text-lime-700 dark:bg-lime-900 dark:text-lime-200',
  },
  {
    id: 'rusle',
    domain: 'erosion',
    domainKey: 'models.domains.erosion',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M3 20h18" strokeLinecap="round" />
        <path d="M6 20l4-10 4 6 4-8 4 12" strokeLinejoin="round" strokeLinecap="round" />
      </svg>
    ),
    gradient: 'from-amber-500 to-orange-700',
    soft: 'bg-amber-50 dark:bg-amber-950/40',
    badge: 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-200',
  },
  {
    id: 'rothc',
    domain: 'carbon',
    domainKey: 'models.domains.carbon',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" strokeLinejoin="round" />
      </svg>
    ),
    gradient: 'from-emerald-500 to-teal-700',
    soft: 'bg-emerald-50 dark:bg-emerald-950/40',
    badge: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-200',
  },
];

/* ================================================================
   MODELS SHOWCASE — colorful 3D cards
   ================================================================ */
export function ModelsShowcase() {
  const { t } = useTranslation();
  return (
    <section className="relative overflow-hidden py-24 lg:py-32">
      <div aria-hidden className="absolute inset-0 -z-10 bg-surface-muted/40" />
      <div
        aria-hidden
        className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_20%_50%,rgba(175,95,30,0.06),transparent_45%),radial-gradient(circle_at_80%_50%,rgba(6,182,212,0.06),transparent_45%)]"
      />

      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <Reveal>
          <div className="mx-auto max-w-2xl text-center">
            <Badge tone="brand" variant="soft" className="mx-auto">{t('models.title')}</Badge>
            <h2 className={cn('mt-4 text-balance text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl', roleClasses.h2)}>
              {t('models.showcaseTitle', 'موتورهای علمی پلتفرم')}
            </h2>
            <p className="mt-4 text-balance text-base text-ink-muted md:text-lg">{t('models.subtitle')}</p>
          </div>
        </Reveal>

        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {MODELS.map((m, i) => (
            <Reveal key={m.id} delay={i * 80}>
              <a href={DASHBOARD_URL} target="_blank" rel="noopener noreferrer" className="group block h-full">
                <div
                  className={cn(
                    'card-3d relative h-full overflow-hidden rounded-2xl border border-ink/10 bg-surface-raised p-6 transition-all duration-500 hover:shadow-elevated',
                    m.soft,
                  )}
                >
                  <div className={cn('absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r', m.gradient)} />

                  <div className="flex items-center justify-between">
                    <div className={cn('grid h-12 w-12 place-items-center rounded-xl', m.badge)}>{m.icon}</div>
                    <span className={cn('rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-wider', m.badge)}>
                      {t(m.domainKey, m.domain)}
                    </span>
                  </div>

                  <h3 className="mt-4 text-lg font-semibold text-ink">
                    {t(`models.${m.id}.name`, m.id.toUpperCase())}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-ink-muted">{t(`models.${m.id}.desc`)}</p>

                  <div className="mt-5 flex items-center gap-2 text-sm font-semibold text-ink-muted transition-colors group-hover:text-ink">
                    <span>{t('models.launchIn', 'اجرا در HyDroMa')}</span>
                    <span aria-hidden className="rtl-flip">→</span>
                  </div>
                </div>
              </a>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
