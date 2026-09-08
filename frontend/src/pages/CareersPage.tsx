import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import CtaBand from '../components/sections/CtaBand';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import { useLang } from '../i18n/LanguageContext';
import { careers } from '../content/pages/partnerscareers';

/** Careers page — values, needed skills, honest hiring status. */
export default function CareersPage() {
  const { lang, t } = useLang();
  const c = careers[lang as 'fa' | 'en'];

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/careers" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />

      <section className="px-4 py-10 sm:px-6" id="values">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <SectionHeading kicker={c.kicker} title={c.valuesTitle} />
          <div className="grid gap-4 lg:grid-cols-3">
            {c.values.map((value, index) => (
              <Reveal key={value.title} delay={index * 0.07}>
                <div className="glass glass-hover h-full rounded-3xl p-6">
                  <h3 className="text-base font-extrabold text-emerald-50">{value.title}</h3>
                  <p className="mt-2 text-sm leading-7 text-emerald-100/60">{value.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="px-4 pb-10 sm:px-6" id="roles">
        <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-2">
          <Reveal>
            <div className="glass h-full rounded-3xl p-8">
              <h2 className="text-lg font-extrabold text-emerald-50">{c.rolesTitle}</h2>
              <ul className="mt-4 flex flex-col gap-3">
                {c.roles.map((role) => (
                  <li key={role} className="flex items-start gap-3 text-sm leading-7 text-emerald-100/65">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-leaf-400" aria-hidden />
                    {role}
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
          <Reveal delay={0.1}>
            <div className="ring-glow flex h-full flex-col justify-center gap-3 rounded-3xl bg-gradient-to-b from-leaf-600/20 to-night-900 p-8">
              <h2 className="text-lg font-extrabold text-emerald-50">{c.openTitle}</h2>
              <p className="text-sm leading-8 text-emerald-100/70">{c.openBody}</p>
            </div>
          </Reveal>
        </div>
      </section>

      <CtaBand />
    </>
  );
}
