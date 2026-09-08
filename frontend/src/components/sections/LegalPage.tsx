import { Link } from 'react-router-dom';
import type { LegalPageContent } from '../../content/site';
import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';

interface LegalPageProps {
  content: LegalPageContent;
}

/** Shared layout for legal pages: version chip, draft note, sections and cross-links. */
export default function LegalPage({ content }: LegalPageProps) {
  const { lang, t } = useLang();

  const siblings = [
    { to: '/terms', label: t.footer.legalLinks.terms },
    { to: '/rules', label: t.footer.legalLinks.rules },
    { to: '/privacy', label: t.footer.legalLinks.privacy },
  ];

  return (
    <>
      <section className="px-4 pb-4 pt-14 sm:px-6 lg:pt-20">
        <Reveal className="mx-auto flex max-w-3xl flex-col items-start gap-4">
          <span className="inline-flex items-center gap-2 rounded-full border border-leaf-500/30 bg-leaf-500/10 px-4 py-1 text-xs font-bold text-leaf-300">
            <span className="h-1.5 w-1.5 rounded-full bg-leaf-400 animate-pulse-soft" aria-hidden />
            {content.kicker}
          </span>
          <h1 className="text-3xl font-extrabold leading-snug text-emerald-50 sm:text-5xl">
            {content.title}
          </h1>
          <p className="max-w-2xl text-base leading-8 text-emerald-100/60">{content.lead}</p>
          <div className="flex flex-wrap items-center gap-2">
            <span className="glass rounded-full px-4 py-1.5 text-xs font-bold text-emerald-100/70" dir="ltr">
              {content.version}
            </span>
            <span className="glass rounded-full px-4 py-1.5 text-xs font-bold text-emerald-100/70">
              {lang === 'fa' ? 'آخرین بازنگری: ' : 'Last reviewed: '}
              {content.updated}
            </span>
          </div>
          <p className="w-full rounded-2xl border border-sand-500/25 bg-sand-500/8 p-4 text-xs leading-6 text-sand-200/90">
            {content.draftNote}
          </p>
        </Reveal>
      </section>

      <section className="px-4 py-10 sm:px-6">
        <div className="mx-auto flex max-w-3xl flex-col gap-5">
          {content.sections.map((section, index) => (
            <Reveal key={section.title} delay={Math.min(index * 0.04, 0.2)}>
              <article className="glass rounded-3xl p-7">
                <h2 className="flex items-baseline gap-2 text-lg font-extrabold text-emerald-50">
                  <span className="text-leaf-400/70" aria-hidden>
                    {new Intl.NumberFormat(lang === 'fa' ? 'fa-IR' : 'en-US').format(index + 1)}.
                  </span>
                  {section.title}
                </h2>
                <div className="mt-3 flex flex-col gap-2.5">
                  {section.body.map((paragraph) => (
                    <p key={paragraph} className="text-sm leading-8 text-emerald-100/70">
                      {paragraph}
                    </p>
                  ))}
                </div>
              </article>
            </Reveal>
          ))}

          {/* cross-links to the other legal pages */}
          <Reveal>
            <nav
              aria-label={t.footer.legalTitle}
              className="glass flex flex-wrap items-center gap-2 rounded-2xl p-4 text-xs"
            >
              <span className="font-bold text-emerald-100/50">{t.footer.legalTitle}:</span>
              {siblings.map((sib) => (
                <Link
                  key={sib.to}
                  to={sib.to}
                  className="rounded-full bg-white/5 px-3 py-1.5 font-bold text-leaf-300 transition-colors hover:bg-leaf-500/15"
                >
                  {sib.label}
                </Link>
              ))}
            </nav>
          </Reveal>
        </div>
      </section>
    </>
  );
}
