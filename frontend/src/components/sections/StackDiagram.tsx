import { useLang } from '../../i18n/LanguageContext';
import Icon from '../ui/Icon';
import Reveal from '../ui/Reveal';
import SectionHeading from '../ui/SectionHeading';

/** Layered architecture diagram: browser → gateway → services → engine → data. */
export default function StackDiagram() {
  const { t, dir } = useLang();
  const layers = t.platform.stack.layers;

  return (
    <section className="px-4 py-14 sm:px-6" id="stack">
      <div className="mx-auto flex max-w-6xl flex-col gap-10">
        <SectionHeading
          kicker={t.platform.kicker}
          title={t.platform.stack.title}
          lead={t.platform.stack.lead}
        />

        <div className="flex flex-col gap-3">
          {layers.map((layer, index) => (
            <Reveal key={layer.title} delay={index * 0.06}>
              <div className="glass glass-hover flex items-center gap-4 rounded-2xl p-4 sm:gap-5 sm:px-6">
                <span className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-aqua-500/12 text-aqua-300">
                  <Icon name={layer.icon} className="h-5 w-5" aria-hidden />
                </span>
                <div className="flex min-w-0 flex-col">
                  <h3 className="text-sm font-extrabold text-emerald-50 sm:text-base">
                    {layer.title}
                  </h3>
                  <p className="text-xs leading-6 text-emerald-100/60 sm:text-sm">
                    {layer.desc}
                  </p>
                </div>
                {index < layers.length - 1 ? (
                  <span
                    className="ms-auto hidden shrink-0 text-leaf-500/40 sm:block"
                    aria-hidden
                  >
                    {dir === 'rtl' ? '↓' : '↓'}
                  </span>
                ) : null}
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
