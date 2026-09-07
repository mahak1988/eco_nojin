import { useTranslation } from 'react-i18next';
import { AnimatedCounter, Reveal } from '@eco/ui';
import { formatNumber } from '@eco/utils';
import { SUPPORTED_LOCALES } from '@eco/config';
import { TOTAL_BACKEND_MODELS } from '@eco/models';

/** Honest, verifiable stats — sourced from the platform itself. */
const STANDARDS_COUNT = 6; // SWAT+, RothC, AquaCrop, RUSLE, HEC-RAS, Pywr

export function GlobalStats() {
  const { t, i18n } = useTranslation();
  const locale = i18n.language === 'fa' ? 'fa-IR' : i18n.language;
  const plus = (n: number) => `${formatNumber(n, { locale, decimals: 0 })}+`;

  const STATS: { node: React.ReactNode; labelKey: string; fallback: string }[] = [
    { node: <AnimatedCounter from={0} to={TOTAL_BACKEND_MODELS} duration={1800} formatter={(v) => `${Math.round(v).toLocaleString(locale)}+`} />, labelKey: 'home.statModels', fallback: 'مدل ثبت‌شده در موتور اجرا' },
    { node: plus(9), labelKey: 'home.statDomains', fallback: 'دامنهٔ علمی' },
    { node: plus(STANDARDS_COUNT), labelKey: 'home.statStandards', fallback: 'مدل استاندارد جهانی' },
    { node: formatNumber(SUPPORTED_LOCALES.length, { locale, decimals: 0 }), labelKey: 'home.statLangs', fallback: 'زبان رابط کاربری' },
  ];

  return (
    <section className="border-y border-ink/10 bg-surface-inverse py-16 text-ink-inverse dark:border-ink/10">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
          {STATS.map((s, i) => (
            <Reveal key={s.labelKey} delay={i * 60}>
              <div className="text-center">
                <div className="text-4xl font-bold tracking-tight text-brand-300 dark:text-brand-200">{s.node}</div>
                <div className="mt-2 text-xs uppercase tracking-wider text-ink-inverse/60">
                  {t(s.labelKey, s.fallback)}
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
