import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import UniversalCard from '../components/ui/UniversalCard';
import { useLang } from '../i18n/LanguageContext';
import { carbon } from '../content/pages/impactcarbon';

const STEP_THEMES: ('leaf' | 'aqua' | 'sand' | 'night')[] = ['leaf', 'aqua', 'sand', 'night'];

/** Carbon page — the credit path, participation and honest status. */
export default function CarbonPage() {
  const { lang, t, dir } = useLang();
  const c = carbon[lang as 'fa' | 'en'];

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/carbon" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />

      <section className="px-4 py-10 sm:px-6" id="path">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <SectionHeading kicker={c.kicker} title={c.howTitle} />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {c.how.map((step, index) => (
              <Reveal key={step.title} delay={index * 0.07}>
                <UniversalCard
                  title={step.title}
                  desc={step.desc}
                  icon="leaf"
                  theme={STEP_THEMES[index % STEP_THEMES.length]}
                  unit={(index + 1).toString()}
                  index={index}
                  flipOnHover={false}
                />
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="px-4 pb-10 sm:px-6" id="participate">
        <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-2">
          <Reveal>
            <div className="glass h-full rounded-3xl p-8">
              <h2 className="text-lg font-extrabold text-[var(--color-night-100)]">{c.participateTitle}</h2>
              <ul className="mt-4 flex flex-col gap-3">
                {c.participate.map((item) => (
                  <li
                    key={item}
                    className="flex items-start gap-3 text-sm leading-7 text-[var(--color-night-200)]/65"
                  >
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--color-leaf-400)]" aria-hidden />
                    {item}
                  </li>
                ))}
              </ul>
              <Link
                to="/contact"
                className="ring-glow mt-6 inline-flex items-center gap-2 rounded-full bg-[var(--color-leaf-500)] px-5 py-2.5 text-xs font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.03]"
              >
                {t.cta.button}
                <ArrowLeft className={`h-3.5 w-3.5 ${dir === 'rtl' ? '' : 'rotate-180'}`} aria-hidden />
              </Link>
            </div>
          </Reveal>

          <Reveal delay={0.1}>
            <div className="ring-glow flex h-full flex-col justify-center gap-3 rounded-3xl bg-gradient-to-b from-leaf-600/20 to-night-900 p-8">
              <h2 className="text-lg font-extrabold text-[var(--color-night-100)]">{c.statusTitle}</h2>
              <p className="text-sm leading-8 text-[var(--color-night-200)]/70">{c.statusBody}</p>
              <Link
                to="/transparency"
                className="inline-flex w-fit items-center gap-2 text-sm font-extrabold text-[var(--color-leaf-300)] hover:text-[var(--color-leaf-200)]"
              >
                {t.footer.quickLinks.transparency}
                <ArrowLeft className={`h-4 w-4 ${dir === 'rtl' ? '' : 'rotate-180'}`} aria-hidden />
              </Link>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
