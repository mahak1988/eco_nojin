import { useLang } from '../../i18n/LanguageContext';
import Icon from '../ui/Icon';
import Reveal from '../ui/Reveal';
import SectionHeading from '../ui/SectionHeading';

/** Five access channels — web, USSD, SMS, messaging bots, voice. */
export default function ChannelsGrid() {
  const { t } = useLang();

  return (
    <section className="px-4 py-16 sm:px-6 lg:py-24" id="channels">
      <div className="mx-auto flex max-w-6xl flex-col gap-12">
        <SectionHeading kicker={t.channels.kicker} title={t.channels.title} lead={t.channels.lead} />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {t.channels.items.map((item, index) => (
            <Reveal key={item.title} delay={index * 0.07}>
              <article className="glass glass-hover flex h-full flex-col items-start gap-3 rounded-3xl p-6">
                <span className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-aqua-500/12 text-aqua-300">
                  <Icon name={item.icon} className="h-5 w-5" aria-hidden />
                </span>
                <h3 className="text-sm font-extrabold text-emerald-50">{item.title}</h3>
                <p className="text-xs leading-6 text-emerald-100/60">{item.desc}</p>
              </article>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
