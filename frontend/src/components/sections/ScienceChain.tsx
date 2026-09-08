import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';
import SectionHeading from '../ui/SectionHeading';

interface ScienceChainProps {
  /** preview = compact chain + model chips with a link; full = adds data sources. */
  variant: 'preview' | 'full';
}

/** The HyDroMa scientific chain: observation → simulation → optimization → decision. */
export default function ScienceChain({ variant }: ScienceChainProps) {
  const { t, dir } = useLang();
  const isFull = variant === 'full';

  return (
    <section className="px-4 py-16 sm:px-6 lg:py-24" id="science">
      <div className="mx-auto flex max-w-6xl flex-col gap-14">
        <SectionHeading kicker={t.science.kicker} title={t.science.title} lead={t.science.lead} />

        {/* chain steps */}
        <ol className="relative grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* connector line (desktop) */}
          <div
            className="absolute inset-x-8 top-9 hidden border-t-2 border-dashed border-leaf-500/25 lg:block"
            aria-hidden
          />
          {t.science.steps.map((step, index) => (
            <Reveal key={step.title} delay={index * 0.1}>
              <li className="glass glass-hover relative flex h-full flex-col gap-3 rounded-3xl p-6">
                <span className="ring-glow inline-flex h-10 w-10 items-center justify-center rounded-full bg-leaf-500 text-base font-extrabold text-night-950">
                  {new Intl.NumberFormat(dir === 'rtl' ? 'fa-IR' : 'en-US').format(index + 1)}
                </span>
                <h3 className="text-base font-extrabold text-emerald-50">{step.title}</h3>
                <p className="text-sm leading-7 text-emerald-100/60">{step.desc}</p>
              </li>
            </Reveal>
          ))}
        </ol>

        {/* models */}
        <div className="flex flex-col gap-5">
          <h3 className="text-sm font-extrabold tracking-wide text-leaf-300/90">
            {t.science.modelsTitle}
          </h3>
          <div className="flex flex-wrap gap-3">
            {t.science.models.map((model, index) => (
              <Reveal key={model.name} delay={index * 0.05}>
                <span
                  className="glass glass-hover flex items-baseline gap-2 rounded-2xl px-5 py-3"
                  dir="ltr"
                >
                  <span className="text-sm font-extrabold text-aqua-300">{model.name}</span>
                  <span
                    className="text-xs text-emerald-100/55"
                    dir={dir === 'rtl' ? 'rtl' : 'ltr'}
                  >
                    {model.desc}
                  </span>
                </span>
              </Reveal>
            ))}
          </div>
        </div>

        {/* data sources (full variant only) */}
        {isFull ? (
          <div className="flex flex-col gap-5">
            <h3 className="text-sm font-extrabold tracking-wide text-leaf-300/90">
              {t.science.dataSourcesTitle}
            </h3>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {t.science.dataSources.map((source, index) => (
                <Reveal key={source.name} delay={index * 0.07}>
                  <div className="glass glass-hover flex h-full flex-col gap-2 rounded-2xl p-5">
                    <span className="text-sm font-extrabold text-aqua-300" dir="ltr">
                      {source.name}
                    </span>
                    <span className="text-xs leading-6 text-emerald-100/60">{source.desc}</span>
                  </div>
                </Reveal>
              ))}
            </div>
          </div>
        ) : (
          <Link
            to="/hydroma"
            className="group inline-flex w-fit items-center gap-2 text-sm font-extrabold text-leaf-300 transition-colors hover:text-leaf-200"
          >
            {t.science.more}
            <ArrowLeft
              className={`h-4 w-4 transition-transform group-hover:-translate-x-1 ${
                dir === 'rtl' ? '' : 'rotate-180'
              }`}
              aria-hidden
            />
          </Link>
        )}
      </div>
    </section>
  );
}
