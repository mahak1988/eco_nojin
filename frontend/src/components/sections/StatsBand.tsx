import { useLang } from '../../i18n/LanguageContext';

/** Slim single-row stats strip (About page) — quiet numbers, no cards. */
export default function StatsBand() {
  const { t } = useLang();

  return (
    <section className="px-4 py-[34px] sm:px-6" aria-label="Key numbers">
      <div className="stats-strip mx-auto max-w-6xl rounded-[21px] border border-white/8 bg-night-900 px-[13px] py-[21px]">
        {t.stats.map((stat) => (
          <div key={stat.label} className="flex flex-col items-center gap-1 px-[13px] text-center">
            <span className="text-lg font-extrabold text-leaf-300">{stat.value}</span>
            <span className="text-[11px] leading-5 text-ink-3">{stat.label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
