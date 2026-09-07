import { useTranslation } from 'react-i18next';

/**
 * Standards & data sources the platform is built on.
 * Factual framing: public datasets/standards we integrate — not endorsements.
 * Apple-style: quiet, static, centered.
 */
const SOURCES = [
  'Sentinel-2', 'ESA', 'NASA POWER', 'ECMWF ERA5', 'SoilGrids', 'FAO AquaCrop',
  'USDA', 'IPCC AR6', 'OpenET', 'CGIAR',
];

export function TrustMarquee() {
  const { t } = useTranslation();
  return (
    <section className="border-t border-ink/5 bg-surface py-16">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <p className="text-center text-xs font-semibold uppercase tracking-[0.2em] text-ink-subtle">
          {t('home.trustLabel', 'بر پایهٔ داده‌ها و استانداردهای جهانی')}
        </p>
        <div className="mx-auto mt-8 flex max-w-4xl flex-wrap items-center justify-center gap-x-8 gap-y-4">
          {SOURCES.map((label) => (
            <span key={label} className="text-sm font-medium text-ink-muted">
              {label}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
