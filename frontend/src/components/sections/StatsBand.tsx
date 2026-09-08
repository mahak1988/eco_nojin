import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';

/** Horizontal band of key platform statistics. */
export default function StatsBand() {
  const { t } = useLang();

  return (
    <section className="px-4 py-10 sm:px-6" aria-label="Key numbers">
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {t.stats.map((stat, index) => (
          <Reveal key={stat.label} delay={index * 0.06}>
            <div className="glass glass-hover flex h-full flex-col items-center gap-2 rounded-2xl px-3 py-6 text-center">
              <span className="text-2xl font-extrabold text-gradient-leaf sm:text-3xl">
                {stat.value}
              </span>
              <span className="text-xs leading-5 text-emerald-100/60">{stat.label}</span>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
