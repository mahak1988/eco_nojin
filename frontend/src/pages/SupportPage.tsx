import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import CtaBand from '../components/sections/CtaBand';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import { useLang } from '../i18n/LanguageContext';
import { support } from '../content/pages/support';

/** Support page — textual channel guides + troubleshooting. */
export default function SupportPage() {
  const { lang, t } = useLang();
  const c = support[lang as 'fa' | 'en'];
  const guides = [c.ussd, c.sms, c.voice];

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/support" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />

      <section className="px-4 py-10 sm:px-6" id="guides">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <SectionHeading kicker={c.kicker} title={c.guidesTitle} />
          <div className="grid gap-4 lg:grid-cols-3">
            {guides.map((guide, index) => (
              <Reveal key={guide.title} delay={index * 0.08}>
                <article className="glass glass-hover flex h-full flex-col gap-4 rounded-3xl p-7">
                  <h3 className="text-lg font-extrabold text-emerald-50">{guide.title}</h3>
                  <ol className="flex flex-col gap-3">
                    {guide.steps.map((step, stepIndex) => (
                      <li key={step} className="flex items-start gap-3">
                        <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-leaf-500/15 text-[11px] font-extrabold text-leaf-300">
                          {new Intl.NumberFormat(lang === 'fa' ? 'fa-IR' : 'en-US').format(stepIndex + 1)}
                        </span>
                        <span className="text-sm leading-7 text-emerald-100/65">{step}</span>
                      </li>
                    ))}
                  </ol>
                </article>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="px-4 pb-10 sm:px-6" id="troubleshooting">
        <div className="mx-auto flex max-w-4xl flex-col gap-6">
          <Reveal>
            <h2 className="text-xl font-extrabold text-emerald-50">{c.troubleshootingTitle}</h2>
          </Reveal>
          {c.troubleshooting.map((item, index) => (
            <Reveal key={item.q} delay={index * 0.05}>
              <div className="glass rounded-2xl p-5">
                <p className="text-sm font-extrabold text-emerald-50">{item.q}</p>
                <p className="mt-1.5 text-sm leading-7 text-emerald-100/60">{item.a}</p>
              </div>
            </Reveal>
          ))}
          <Reveal>
            <div className="rounded-2xl border border-aqua-500/25 bg-aqua-500/8 p-5">
              <p className="text-sm font-extrabold text-aqua-200">{c.moreTitle}</p>
              <p className="mt-1 text-xs leading-6 text-aqua-200/80">{c.moreBody}</p>
            </div>
          </Reveal>
        </div>
      </section>

      <CtaBand />
    </>
  );
}
