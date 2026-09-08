import { Link } from 'react-router-dom';
import { Info, ScrollText } from 'lucide-react';
import Seo from '../components/ui/Seo';
import Reveal from '../components/ui/Reveal';
import CtaBand from '../components/sections/CtaBand';
import { useLang } from '../i18n/LanguageContext';
import { declaration } from '../content/pages/declaration';

/** Declaration page — the official statement, published verbatim (report 64). */
export default function DeclarationPage() {
  const { lang, t } = useLang();
  const c = declaration[lang as 'fa' | 'en'];

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/declaration" />

      <section className="px-4 pb-4 pt-14 sm:px-6 lg:pt-20">
        <Reveal className="mx-auto flex max-w-3xl flex-col items-start gap-4">
          <span className="inline-flex items-center gap-2 rounded-full border border-leaf-500/30 bg-leaf-500/10 px-4 py-1 text-xs font-bold text-leaf-300">
            <ScrollText className="h-3.5 w-3.5" aria-hidden />
            {c.kicker}
          </span>
          <h1 className="text-3xl font-extrabold leading-snug text-emerald-50 sm:text-4xl lg:text-[2.6rem]">
            {c.title}
          </h1>
          <p className="max-w-2xl text-base leading-8 text-emerald-100/60">{c.lead}</p>
          <div className="flex flex-wrap items-center gap-2">
            <span className="glass rounded-full px-4 py-1.5 text-xs font-bold text-emerald-100/70" dir="ltr">
              {c.version}
            </span>
            <span className="glass rounded-full px-4 py-1.5 text-xs font-bold text-emerald-100/70">
              {c.updated}
            </span>
          </div>
        </Reveal>
      </section>

      <section className="px-4 pb-4 sm:px-6">
        <div className="mx-auto flex max-w-3xl flex-col gap-3">
          <div className="flex items-start gap-3 rounded-2xl border border-sand-500/25 bg-sand-500/8 p-4">
            <Info className="mt-0.5 h-5 w-5 shrink-0 text-sand-300" aria-hidden />
            <p className="text-xs leading-6 text-sand-200/90">
              {c.legalNote}{' '}
              <Link to="/terms" className="font-bold text-leaf-300 hover:underline">
                {t.footer.legalLinks.terms}
              </Link>{' '}
              ·{' '}
              <Link to="/rules" className="font-bold text-leaf-300 hover:underline">
                {t.footer.legalLinks.rules}
              </Link>
            </p>
          </div>
          <p className="rounded-2xl border border-aqua-500/25 bg-aqua-500/8 p-4 text-xs leading-6 text-aqua-200/90">
            {c.refsNote}{' '}
            <Link to="/transparency" className="font-bold text-aqua-300 hover:underline">
              {t.footer.quickLinks.transparency}
            </Link>
          </p>
        </div>
      </section>

      <section className="px-4 py-8 sm:px-6">
        <div className="mx-auto flex max-w-3xl flex-col gap-8">
          {c.sections.map((section, index) => (
            <Reveal key={section.heading} delay={Math.min(index * 0.03, 0.15)}>
              <article className="flex flex-col gap-4">
                <h2 className="text-xl font-extrabold leading-snug text-emerald-50 sm:text-2xl">
                  {section.heading}
                </h2>
                {section.paragraphs.map((paragraph) => (
                  <p key={paragraph} className="text-[15px] leading-9 text-emerald-50/80">
                    {paragraph}
                  </p>
                ))}
                {section.bullets ? (
                  <ul className="flex flex-col gap-3">
                    {section.bullets.map((bullet) => (
                      <li
                        key={bullet}
                        className="glass flex items-start gap-3 rounded-2xl p-4 text-sm leading-7 text-emerald-50/85"
                      >
                        <span
                          className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-leaf-400"
                          aria-hidden
                        />
                        {bullet}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </article>
            </Reveal>
          ))}

          {/* sign-off */}
          <Reveal>
            <div className="ring-glow flex flex-col items-center gap-2 rounded-3xl bg-gradient-to-b from-leaf-600/20 to-night-900 p-8 text-center">
              {c.signoff.map((line, index) => (
                <p
                  key={line}
                  className={
                    index === 0
                      ? 'text-lg font-extrabold text-emerald-50'
                      : index === c.signoff.length - 1
                        ? 'text-xs font-bold text-emerald-100/40'
                        : 'text-sm font-bold text-emerald-100/70'
                  }
                >
                  {line}
                </p>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      <CtaBand />
    </>
  );
}
