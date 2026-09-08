import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import CtaBand from '../components/sections/CtaBand';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import { useLang } from '../i18n/LanguageContext';
import { partners } from '../content/pages/partnerscareers';

/** Partners page — who we seek, partnership models, CTA. */
export default function PartnersPage() {
  const { lang, t } = useLang();
  const c = partners[lang as 'fa' | 'en'];

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/partners" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />

      <section className="px-4 py-10 sm:px-6" id="who">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <SectionHeading kicker={c.kicker} title={c.whoTitle} />
          <div className="grid gap-4 sm:grid-cols-2">
            {c.who.map((item, index) => (
              <Reveal key={item.title} delay={(index % 2) * 0.07}>
                <div className="glass glass-hover h-full rounded-3xl p-6">
                  <h3 className="text-base font-extrabold text-emerald-50">{item.title}</h3>
                  <p className="mt-2 text-sm leading-7 text-emerald-100/60">{item.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="px-4 pb-10 sm:px-6" id="models">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <SectionHeading kicker={c.kicker} title={c.modelsTitle} />
          <div className="grid gap-4 lg:grid-cols-3">
            {c.models.map((model, index) => (
              <Reveal key={model.title} delay={index * 0.07}>
                <div className="ring-glow flex h-full flex-col gap-2 rounded-3xl bg-gradient-to-b from-leaf-600/15 to-night-900 p-6">
                  <h3 className="text-base font-extrabold text-emerald-50">{model.title}</h3>
                  <p className="text-sm leading-7 text-emerald-100/65">{model.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
          <Reveal>
            <div className="glass rounded-3xl p-8">
              <h2 className="text-lg font-extrabold text-emerald-50">{c.ctaTitle}</h2>
              <p className="mt-2 text-sm leading-8 text-emerald-100/65">{c.ctaBody}</p>
            </div>
          </Reveal>
        </div>
      </section>

      <CtaBand />
    </>
  );
}
