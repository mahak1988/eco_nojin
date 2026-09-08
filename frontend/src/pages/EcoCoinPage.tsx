import { Link } from 'react-router-dom';
import { ShieldCheck, Sparkles } from 'lucide-react';
import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import { useLang } from '../i18n/LanguageContext';
import { ecoCoin } from '../content/pages/ecocoin';

/** Eco Coin page — two-phase framework + issuance chain + honest gate. */
export default function EcoCoinPage() {
  const { lang, t, dir } = useLang();
  const c = ecoCoin[lang as 'fa' | 'en'];

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/eco-coin" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />

      {/* phases */}
      <section className="px-4 py-10 sm:px-6" id="phases">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <SectionHeading kicker={c.kicker} title={c.phasesTitle} />
          <div className="grid gap-4 lg:grid-cols-2">
            {c.phases.map((phase, index) => (
              <Reveal key={phase.tag} delay={index * 0.08}>
                <div
                  className={`glass glass-hover h-full rounded-3xl p-7 ${
                    index === 0 ? 'border-leaf-500/30 bg-leaf-500/8' : 'border-sand-500/25 bg-sand-500/6'
                  }`}
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`rounded-full px-3 py-1 text-[11px] font-bold ${
                        index === 0 ? 'bg-leaf-500/15 text-leaf-300' : 'bg-sand-500/15 text-sand-300'
                      }`}
                    >
                      {phase.tag}
                    </span>
                    <span
                      className={`rounded-full px-3 py-1 text-[11px] font-bold ${
                        index === 0 ? 'bg-aqua-500/15 text-aqua-300' : 'bg-white/8 text-emerald-100/60'
                      }`}
                    >
                      {phase.status}
                    </span>
                  </div>
                  <h3 className="mt-3 text-lg font-extrabold text-emerald-50">{phase.title}</h3>
                  <p className="mt-2 text-sm leading-8 text-emerald-100/65">{phase.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* issuance chain */}
      <section className="px-4 py-10 sm:px-6" id="chain">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <SectionHeading kicker={c.kicker} title={c.chainTitle} lead={c.chainLead} />
          <ol className="relative grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <div
              className="absolute inset-x-10 top-9 hidden border-t-2 border-dashed border-leaf-500/25 lg:block"
              aria-hidden
            />
            {c.chain.map((step, index) => (
              <Reveal key={step.title} delay={index * 0.07}>
                <li className="glass glass-hover relative flex h-full flex-col gap-2 rounded-3xl p-5">
                  <span className="ring-glow inline-flex h-9 w-9 items-center justify-center rounded-full bg-leaf-500 text-xs font-extrabold text-night-950">
                    {new Intl.NumberFormat(lang === 'fa' ? 'fa-IR' : 'en-US').format(index + 1)}
                  </span>
                  <h3 className="mt-1 text-sm font-extrabold text-emerald-50">{step.title}</h3>
                  <p className="text-xs leading-6 text-emerald-100/60">{step.desc}</p>
                </li>
              </Reveal>
            ))}
          </ol>
        </div>
      </section>

      {/* commitments + gate */}
      <section className="px-4 py-6 sm:px-6">
        <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-2">
          <Reveal>
            <div className="glass h-full rounded-3xl p-7">
              <h2 className="flex items-center gap-2 text-lg font-extrabold text-emerald-50">
                <ShieldCheck className="h-5 w-5 text-leaf-400" aria-hidden />
                {c.commitmentsTitle}
              </h2>
              <ul className="mt-4 flex flex-col gap-3">
                {c.commitments.map((item) => (
                  <li key={item} className="flex items-start gap-3 text-sm leading-7 text-emerald-100/65">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-leaf-400" aria-hidden />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
          <Reveal delay={0.08}>
            <div className="ring-glow flex h-full flex-col justify-center gap-3 rounded-3xl bg-gradient-to-b from-sand-500/15 to-night-900 p-7">
              <h2 className="flex items-center gap-2 text-lg font-extrabold text-emerald-50">
                <Sparkles className="h-5 w-5 text-sand-300" aria-hidden />
                {c.gateTitle}
              </h2>
              <p className="text-sm leading-8 text-emerald-100/70">{c.gateBody}</p>
              <div className="mt-2 flex flex-wrap gap-2 text-xs font-bold">
                <Link to="/terms" className="rounded-full bg-white/8 px-4 py-1.5 text-emerald-100/70 hover:bg-white/15">
                  {t.footer.legalLinks.terms}
                </Link>
                <Link to="/transparency" className="rounded-full bg-white/8 px-4 py-1.5 text-emerald-100/70 hover:bg-white/15">
                  {t.footer.quickLinks.transparency}
                </Link>
                <Link to="/carbon" className="rounded-full bg-white/8 px-4 py-1.5 text-emerald-100/70 hover:bg-white/15">
                  {dir === 'rtl' ? 'کربن' : 'Carbon'}
                </Link>
              </div>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
