import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';
import UniversalCard from '../ui/UniversalCard';

/** Horizontal band of key platform statistics — animated 3D cards. */
export default function StatsBand() {
  const { t } = useLang();
  const themes = ['aqua', 'leaf', 'sand', 'aqua', 'leaf', 'sand'];

  return (
    <section className="px-4 py-10 sm:px-6" aria-label="Key numbers">
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {t.stats.map((stat, index) => (
          <Reveal key={stat.label} delay={index * 0.06}>
            <UniversalCard
              title={stat.value}
              desc={stat.label}
              theme={themes[index] as 'leaf' | 'aqua' | 'sand'}
              index={index}
              flipOnHover={false}
            />
          </Reveal>
        ))}
      </div>
    </section>
  );
}
