import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';
import SectionHeading from '../ui/SectionHeading';
import UniversalCard from '../ui/UniversalCard';

/** Three platform differentiators band. */
export default function WhyBand() {
  const { t } = useLang();
  const themes = ['leaf', 'aqua', 'sand'];

  return (
    <section className="px-4 py-16 sm:px-6" id="why">
      <div className="mx-auto flex max-w-6xl flex-col gap-12">
        <SectionHeading kicker={t.why.kicker} title={t.why.title} />
        <div className="grid gap-4 lg:grid-cols-3">
          {t.why.items.map((item, index) => (
            <Reveal key={item.title} delay={index * 0.08}>
              <UniversalCard
                title={item.title}
                desc={item.desc}
                icon={item.icon}
                theme={themes[index] as 'leaf' | 'aqua' | 'sand'}
                badge={(index + 1).toString()}
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
