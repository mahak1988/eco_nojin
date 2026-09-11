import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';
import SectionHeading from '../ui/SectionHeading';
import UniversalCard from '../ui/UniversalCard';

/** Three trust pillars band. */
export default function TrustBand() {
  const { t } = useLang();
  const themes = ['leaf', 'aqua', 'sand', 'leaf'];

  return (
    <section className="px-4 py-16 sm:px-6" id="trust">
      <div className="mx-auto flex max-w-6xl flex-col gap-12">
        <SectionHeading kicker={t.trust.kicker} title={t.trust.title} lead={t.trust.lead} />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {t.trust.items.map((item, index) => (
            <Reveal key={item.title} delay={(index % 4) * 0.07}>
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
