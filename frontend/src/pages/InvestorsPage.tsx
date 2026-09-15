import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import { useLang } from '../i18n/LanguageContext';
import { investors } from '../content/pages/investors';

/** Investors page — public-safe pitch summary; deck via contact. */
export default function InvestorsPage() {
  const { lang, t, dir } = useLang();
  const c = investors[lang as 'fa' | 'en'];

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/investors" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />

      <section className="px-4 py-10 sm:px-6" id="problem">
        <div className="mx-auto flex max-w-6xl flex-col gap-10">
          <SectionHeading kicker={c.kicker} title={c.problemTitle} />
          <div className="grid gap-4 lg:grid-cols-3">
            {c.problem.map((item, index) => (
              <Reveal key={item.title} delay={index * 0.07}>
                <div className="glass glass-hover h-full rounded-3xl p-6">
                  <h3 className="text-base font-extrabold text-[var(--color-leaf-300)]">{item.title}</h3>
                  <p className="mt-2 text-sm leading-7 text-[var(--color-night-200)]/60">{item.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="px-4 pb-10 sm:px-6" id="solution">
        <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-2">
          <Reveal>
            <div className="glass h-full rounded-3xl p-8">
              <h2 className="text-lg font-extrabold text-[var(--color-night-100)]">{c.solutionTitle}</h2>
              <ul className="mt-4 flex flex-col gap-3">
                {c.solution.map((item) => (
                  <li key={item} className="flex items-start gap-3 text-sm leading-7 text-[var(--color-night-200)]/65">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--color-leaf-400)]" aria-hidden />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
          <Reveal delay={0.08}>
            <div className="glass h-full rounded-3xl p-8">
              <h2 className="text-lg font-extrabold text-[var(--color-night-100)]">{c.statusTitle}</h2>
              <ul className="mt-4 flex flex-col gap-3">
                {c.status.map((item) => (
                  <li key={item} className="flex items-start gap-3 text-sm leading-7 text-[var(--color-night-200)]/65">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--color-aqua-400)]" aria-hidden />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
        </div>
      </section>

      <section className="px-4 pb-10 sm:px-6" id="round">
        <Reveal className="mx-auto max-w-4xl">
          <div className="ring-glow flex flex-col items-start gap-4 rounded-[2rem] bg-gradient-to-b from-leaf-600/25 to-night-900 p-8 sm:p-10">
            <h2 className="text-2xl font-extrabold text-[var(--color-night-100)]">{c.roundTitle}</h2>
            <p className="text-sm leading-8 text-[var(--color-night-200)]/70">{c.roundBody}</p>
            <a
              href={`mailto:${t.about.email}?subject=${encodeURIComponent(`[${c.kicker}] Pitch deck request`)}`}
              className="ring-glow inline-flex items-center gap-2 rounded-full bg-[var(--color-leaf-500)] px-6 py-3 text-sm font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.03]"
            >
              {c.deckCta}
              <ArrowLeftIcon dir={dir} />
            </a>
          </div>
        </Reveal>
      </section>
    </>
  );
}

function ArrowLeftIcon({ dir }: { dir: 'rtl' | 'ltr' }) {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
      className={dir === 'rtl' ? '' : 'rotate-180'}
    >
      <path d="M19 12H5" />
      <path d="m12 19-7-7 7-7" />
    </svg>
  );
}
