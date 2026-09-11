import { CheckCircle2, ScrollText } from 'lucide-react';
import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import { useLang } from '../i18n/LanguageContext';

/** Transparency page — phase timeline, verification chain and public-report promise. */
export default function TransparencyPage() {
  const { t } = useLang();
  const c = t.transparency;

  return (
    <>
      <Seo
        title={`${t.transparency.title} | ${t.brand.name}`}
        description={t.transparency.lead}
        path="/transparency"
      />
      <PageHeader
        kicker={t.transparency.kicker}
        title={t.transparency.title}
        lead={t.transparency.lead}
      />

      {/* phases timeline */}
      <section className="px-4 py-10 sm:px-6" id="phases">
        <div className="mx-auto flex max-w-5xl flex-col gap-8">
          <SectionHeading
            kicker={t.transparency.kicker}
            title={t.transparency.phasesTitle}
            lead={t.transparency.phasesNote}
          />
          <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {t.transparency.phases.map((phase, index) => (
              <Reveal key={phase.id} delay={index * 0.04}>
                <li className="glass glass-hover flex h-full flex-col gap-2 rounded-2xl p-5">
                  <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-leaf-500)]/15 text-xs font-extrabold text-[var(--color-leaf-300)]">
                    {phase.id}
                  </span>
                  <h3 className="text-sm font-extrabold text-[var(--color-night-100)]">{phase.title}</h3>
                  <p className="text-xs leading-6 text-[var(--color-night-200)]/60">{phase.desc}</p>
                </li>
              </Reveal>
            ))}
          </ol>
        </div>
      </section>

      {/* verification chain */}
      <section className="px-4 pb-10 sm:px-6" id="verification">
        <div className="mx-auto max-w-5xl">
          <Reveal>
            <div className="relative overflow-hidden rounded-[2rem] border border-[var(--color-leaf-500)]/20 bg-gradient-to-br from-night-800 via-night-900 to-night-950 p-8 sm:p-10">
              <div
                className="absolute -top-20 end-[-6%] h-56 w-56 rounded-full opacity-25 blur-[100px]"
                style={{ background: 'radial-gradient(circle, #2fb36b 0%, transparent 70%)' }}
                aria-hidden
              />
              <h2 className="text-2xl font-extrabold text-[var(--color-night-100)] sm:text-3xl">
                {t.transparency.verificationTitle}
              </h2>
              <ul className="mt-6 flex flex-col gap-3">
                {t.transparency.verification.map((item) => (
                  <li key={item} className="glass flex items-start gap-3 rounded-2xl p-4">
                    <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-[var(--color-leaf-400)]" aria-hidden />
                    <span className="text-sm leading-7 text-[var(--color-night-100)]/85">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
        </div>
      </section>

      {/* commitments (declaration article 3) */}
      <section className="px-4 pb-10 sm:px-6" id="commitments">
        <div className="mx-auto max-w-5xl">
          <Reveal>
            <h2 className="mb-6 flex items-center gap-2 text-xl font-extrabold text-[var(--color-night-100)] sm:text-2xl">
              <ScrollText className="h-5 w-5 text-[var(--color-sand-300)]" aria-hidden />
              {c.commitmentsTitle}
            </h2>
          </Reveal>
          <div className="grid gap-3 sm:grid-cols-2">
            {c.commitments.map((item, index) => (
              <Reveal key={item} delay={(index % 2) * 0.05}>
                <div className="glass flex h-full items-start gap-3 rounded-2xl p-4">
                  <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-[var(--color-sand-300)]" aria-hidden />
                  <span className="text-sm leading-7 text-[var(--color-night-100)]/85">{item}</span>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* reports promise */}
      <section className="px-4 pb-10 sm:px-6">
        <Reveal className="mx-auto max-w-3xl">
          <p className="rounded-2xl border border-[var(--color-aqua-500)]/25 bg-[var(--color-aqua-500)]/8 p-5 text-center text-xs leading-6 text-[var(--color-aqua-200)]/90">
            {t.transparency.reportsNote}
          </p>
        </Reveal>
      </section>
    </>
  );
}
