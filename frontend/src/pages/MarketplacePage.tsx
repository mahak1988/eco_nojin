import { Link } from 'react-router-dom';
import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import { useLang } from '../i18n/LanguageContext';
import { marketplace } from '../content/pages/marketreresources';

/** Marketplace page — honest preview of the marketplace module. */
export default function MarketplacePage() {
  const { lang, t } = useLang();
  const c = marketplace[lang as 'fa' | 'en'];

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/marketplace" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />

      <section className="px-4 py-10 sm:px-6" id="features">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <SectionHeading kicker={c.kicker} title={c.featuresTitle} />
          <div className="grid gap-4 lg:grid-cols-3">
            {c.features.map((feature, index) => (
              <Reveal key={feature.title} delay={index * 0.07}>
                <div className="glass glass-hover h-full rounded-3xl p-6">
                  <h3 className="text-base font-extrabold text-emerald-50">{feature.title}</h3>
                  <p className="mt-2 text-sm leading-7 text-emerald-100/60">{feature.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="px-4 pb-10 sm:px-6" id="how">
        <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-2">
          <Reveal>
            <div className="glass h-full rounded-3xl p-8">
              <h2 className="text-lg font-extrabold text-emerald-50">{c.howTitle}</h2>
              <ol className="mt-4 flex flex-col gap-3">
                {c.how.map((step, index) => (
                  <li key={step} className="flex items-start gap-3 text-sm leading-7 text-emerald-100/65">
                    <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-leaf-500/15 text-[11px] font-extrabold text-leaf-300">
                      {new Intl.NumberFormat(lang === 'fa' ? 'fa-IR' : 'en-US').format(index + 1)}
                    </span>
                    {step}
                  </li>
                ))}
              </ol>
            </div>
          </Reveal>
          <Reveal delay={0.08}>
            <div className="ring-glow flex h-full flex-col justify-center gap-3 rounded-3xl bg-gradient-to-b from-leaf-600/20 to-night-900 p-8">
              <h2 className="text-lg font-extrabold text-emerald-50">{c.statusTitle}</h2>
              <p className="text-sm leading-8 text-emerald-100/70">{c.statusBody}</p>
              <Link
                to="/contact"
                className="mt-1 w-fit rounded-full bg-leaf-500 px-5 py-2.5 text-xs font-extrabold text-night-950 transition-transform hover:scale-[1.03]"
              >
                {t.cta.button}
              </Link>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
