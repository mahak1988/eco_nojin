import { useLang } from '../../i18n/LanguageContext';
import Icon from '../ui/Icon';
import Reveal from '../ui/Reveal';
import SectionHeading from '../ui/SectionHeading';

/** Three platform differentiators band. */
export default function WhyBand() {
  const { t } = useLang();

  return (
    <section className="px-4 py-16 sm:px-6" id="why">
      <div className="mx-auto flex max-w-6xl flex-col gap-12">
        <SectionHeading kicker={t.why.kicker} title={t.why.title} />
        <div className="grid gap-4 lg:grid-cols-3">
          {t.why.items.map((item, index) => (
            <Reveal key={item.title} delay={index * 0.08}>
              <article className="glass glass-hover relative h-full overflow-hidden rounded-3xl p-7">
                <span
                  className="absolute -top-6 end-[-8%] text-[5.5rem] font-extrabold leading-none text-leaf-500/8 select-none"
                  aria-hidden
                >
                  {index + 1}
                </span>
                <span className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-leaf-500/12 text-leaf-300">
                  <Icon name={item.icon} className="h-6 w-6" aria-hidden />
                </span>
                <h3 className="mt-4 text-lg font-extrabold text-emerald-50">{item.title}</h3>
                <p className="mt-2 text-sm leading-7 text-emerald-100/60">{item.desc}</p>
              </article>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
