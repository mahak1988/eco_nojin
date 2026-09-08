import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import FieldGallery from '../components/sections/FieldGallery';
import NdviConceptChart from '../components/visuals/NdviConceptChart';
import CtaBand from '../components/sections/CtaBand';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import { useLang } from '../i18n/LanguageContext';
import { impact } from '../content/pages/impactcarbon';

/** Impact page — defined metrics, honest "numbers arrive with the pilot". */
export default function ImpactPage() {
  const { lang, t } = useLang();
  const c = impact[lang as 'fa' | 'en'];

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/impact" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />

      <section className="px-4 py-10 sm:px-6" id="metrics">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <SectionHeading kicker={c.kicker} title={c.metricsTitle} lead={c.metricsNote} />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {c.metrics.map((metric, index) => (
              <Reveal key={metric.name} delay={(index % 3) * 0.07}>
                <article className="glass glass-hover flex h-full flex-col gap-2 rounded-3xl p-6">
                  <span className="w-fit rounded-full border border-aqua-500/30 bg-aqua-500/10 px-3 py-1 text-[11px] font-bold text-aqua-300" dir="ltr">
                    {metric.unit}
                  </span>
                  <h3 className="mt-1 text-base font-extrabold text-emerald-50">{metric.name}</h3>
                  <p className="text-xs leading-6 text-emerald-100/60">{metric.desc}</p>
                  <span className="mt-auto pt-3 text-[11px] font-bold tracking-wide text-sand-300/80">
                    {lang === 'fa' ? 'پس از پایلوت' : 'After the pilot'}
                  </span>
                </article>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="px-4 pb-10 sm:px-6">
        <Reveal className="mx-auto max-w-4xl">
          <div className="glass rounded-3xl p-8">
            <h2 className="text-lg font-extrabold text-emerald-50">{c.methodTitle}</h2>
            <p className="mt-3 text-sm leading-8 text-emerald-100/65">{c.methodBody}</p>
          </div>
        </Reveal>
      </section>

      {/* gallery + sample chart */}
      <section className="px-4 pb-10 sm:px-6" id="gallery">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <SectionHeading
            kicker={c.kicker}
            title={lang === 'fa' ? 'گالری میدان و پایش' : 'Field gallery & monitoring'}
            lead={
              lang === 'fa'
                ? 'تصویری از چیزی که پایش می‌کنیم: از اراضی حاشیه‌ای تا تالاب بازگردانده — و روند نمونهٔ شاخص پوشش گیاهی.'
                : 'A glimpse of what we monitor: from marginal lands to restored wetlands — and a sample vegetation-index trend.'
            }
          />
          <FieldGallery />
          <NdviConceptChart />
        </div>
      </section>

      <CtaBand />
    </>
  );
}
