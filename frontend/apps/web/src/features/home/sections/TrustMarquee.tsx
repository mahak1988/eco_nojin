import { useTranslation } from 'react-i18next';

/**
 * Standards & data sources the platform is built on.
 * Factual framing: these are the public datasets/standards we integrate —
 * not endorsements or partnerships.
 */
const SOURCES = [
  'Sentinel-2', 'ESA', 'NASA POWER', 'ECMWF ERA5', 'SoilGrids', 'FAO AquaCrop',
  'USDA', 'IPCC AR6', 'OpenET', 'CGIAR',
];

export function TrustMarquee() {
  const { t } = useTranslation();
  const loop = [...SOURCES, ...SOURCES];
  return (
    <section className="overflow-hidden border-b border-ink/10 bg-surface py-10">
      <div className="mx-auto w-full max-w-content px-4 sm:px-6 lg:px-8">
        <p className="text-center text-xs font-semibold uppercase tracking-[0.2em] text-ink-muted">
          {t('home.trustLabel', 'بر پایهٔ داده‌ها و استانداردهای جهانی')}
        </p>
      </div>
      <div className="relative mt-6">
        <div className="pointer-events-none absolute inset-y-0 start-0 z-10 w-24 bg-gradient-to-r from-surface to-transparent" />
        <div className="pointer-events-none absolute inset-y-0 end-0 z-10 w-24 bg-gradient-to-l from-surface to-transparent" />
        <div className="marquee gap-12">
          {loop.map((label, i) => (
            <span key={`${label}-${i}`} className="whitespace-nowrap text-lg font-semibold tracking-tight text-ink-muted/70">
              {label}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
