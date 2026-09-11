import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';
import SectionHeading from '../ui/SectionHeading';
import UniversalCard from '../ui/UniversalCard';

/** Five access channels — web, USSD, SMS, messaging bots, voice. */
export default function ChannelsGrid() {
  const { t } = useLang();
  const themes = ['aqua', 'aqua', 'aqua', 'sand', 'leaf'];

  return (
    <section className="px-4 py-16 sm:px-6 lg:py-24" id="channels">
      <div className="mx-auto flex max-w-6xl flex-col gap-12">
        <SectionHeading kicker={t.channels.kicker} title={t.channels.title} lead={t.channels.lead} />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {t.channels.items.map((item, index) => (
            <Reveal key={item.title} delay={index * 0.07}>
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
