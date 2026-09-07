import { useTranslation } from 'react-i18next';
import { Reveal } from '@eco/ui';
import { DASHBOARD_URL } from '@eco/config';
import { cn } from '@eco/utils';
import { roleClasses } from '@eco/ui/tokens';

/* ================================================================
   DATA
   ================================================================ */
const MODELS = [
  {
    id: 'swat',
    domainKey: 'models.domains.water',
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    id: 'pywr',
    domainKey: 'models.domains.water',
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <circle cx="6" cy="6" r="3" /><circle cx="18" cy="6" r="3" /><circle cx="12" cy="18" r="3" />
        <path d="M8.5 7.5L10.5 16.5M15.5 7.5L13.5 16.5M6 9h12" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    id: 'hecras',
    domainKey: 'models.domains.hydraulic',
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M3 12h4l3-9 4 18 3-9h4" strokeLinejoin="round" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    id: 'aquacrop',
    domainKey: 'models.domains.crop',
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M12 22V12" strokeLinecap="round" />
        <path d="M12 12c-2-4-6-5-6-5s3 2 6-2c3 4 6 2 6 2s-4-1-6-5z" strokeLinejoin="round" />
        <path d="M12 16c1.5-3 4.5-4 4.5-4s-2 1-4.5-2z" strokeLinejoin="round" opacity="0.5" />
      </svg>
    ),
  },
  {
    id: 'rusle',
    domainKey: 'models.domains.erosion',
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M3 20h18" strokeLinecap="round" />
        <path d="M6 20l4-10 4 6 4-8 4 12" strokeLinejoin="round" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    id: 'rothc',
    domainKey: 'models.domains.carbon',
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" strokeLinejoin="round" />
      </svg>
    ),
  },
];

/* ================================================================
   MODELS SHOWCASE — Apple-style gray tiles on white
   ================================================================ */
export function ModelsShowcase() {
  const { t } = useTranslation();
  return (
    <section className="relative bg-surface py-24 lg:py-32">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <Reveal>
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-sm font-medium text-ink-subtle">{t('models.title')}</p>
            <h2 className={cn('mt-3 text-balance text-4xl font-bold tracking-tight sm:text-5xl', roleClasses.h2)}>
              {t('models.showcaseTitle', 'موتورهای علمی پلتفرم')}
            </h2>
            <p className="mt-4 text-balance text-base text-ink-muted md:text-lg">{t('models.subtitle')}</p>
          </div>
        </Reveal>

        <div className="mt-16 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {MODELS.map((m, i) => (
            <Reveal key={m.id} delay={i * 60}>
              <a href={DASHBOARD_URL} target="_blank" rel="noopener noreferrer" className="group block h-full">
                <div className="card-3d flex h-full flex-col rounded-[28px] bg-surface-muted p-8">
                  <div className="grid h-12 w-12 place-items-center rounded-2xl bg-surface text-brand-600 shadow-sm">
                    {m.icon}
                  </div>
                  <h3 className="mt-6 text-xl font-semibold tracking-tight text-ink">
                    {t(`models.${m.id}.name`, m.id.toUpperCase())}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-ink-muted">{t(`models.${m.id}.desc`)}</p>
                  <span className="mt-auto pt-6 text-sm text-ink-subtle">{t(m.domainKey, '')}</span>
                  <span className="mt-1 inline-flex items-center gap-1 text-sm link-apple">
                    {t('models.launchIn', 'اجرا در HyDroMa')}
                    <span aria-hidden className="rtl-flip">‹</span>
                  </span>
                </div>
              </a>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
