import { useLang } from '../../i18n/LanguageContext';
import Icon from '../ui/Icon';
import Reveal from '../ui/Reveal';
import SectionHeading from '../ui/SectionHeading';

/** Six capability cards covering the full restoration loop. */
export default function CapabilityGrid() {
  const { t } = useLang();

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
              <article className="glass glass-hover group flex h-full flex-col gap-4 rounded-3xl p-7">
                <span className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-leaf-500/12 text-leaf-300 transition-colors group-hover:bg-leaf-500/20">
                  <Icon name={item.icon} className="h-6 w-6" aria-hidden />
                </span>
                <h3 className="text-lg font-extrabold text-emerald-50">{item.title}</h3>
                <p className="text-sm leading-7 text-emerald-100/60">{item.desc}</p>
              </article>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
