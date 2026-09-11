import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';
import UniversalCard from '../ui/UniversalCard';
import SectionHeading from '../ui/SectionHeading';

/** Six capability cards covering the full restoration loop. */
export default function CapabilityGrid() {
  const { t } = useLang();
  const themes = ['leaf', 'aqua', 'sand', 'leaf', 'aqua', 'sand'];

  return (
    <section className="px-4 py-16 sm:px-6 lg:py-24" id="capabilities">
      <div className="mx-auto flex max-w-6xl flex-col gap-12">
        <SectionHeading
          kicker={t.capabilities.kicker}
          title={t.capabilities.title}
          lead={t.capabilities.lead}
        />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {t.capabilities.items.map((item, index) => (
            <Reveal key={item.title} delay={(index % 3) * 0.08}>
              <UniversalCard
                title={item.title}
                desc={item.desc}
                icon={item.icon}
                theme={themes[index] as 'leaf' | 'aqua' | 'sand'}
                index={index}
                flipOnHover={false}
              />
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
