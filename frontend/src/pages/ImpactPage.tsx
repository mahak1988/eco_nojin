import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import LiveCounters from '../components/visuals/LiveCounters';
import MrvCycleChart from '../components/visuals/MrvCycleChart';
import UniversalCard from '../components/ui/UniversalCard';
import ImpactTimeSeries from '../components/visuals/ImpactTimeSeries';
import RechartsImpactChart from '../components/visuals/RechartsImpactChart';
import SatelliteMap from '../components/visuals/SatelliteMap';
import FieldGallery from '../components/sections/FieldGallery';
import NdviConceptChart from '../components/visuals/NdviConceptChart';
import ImpactReportBox from '../components/sections/ImpactReportBox';
import ImpactDataProvenance from '../components/sections/ImpactDataProvenance';
import CtaBand from '../components/sections/CtaBand';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import { useLang } from '../i18n/LanguageContext';
import { impact } from '../content/pages/impactcarbon';

const METRIC_THEMES = ['leaf', 'aqua', 'sand', 'leaf', 'aqua', 'sand', 'leaf', 'aqua', 'sand', 'leaf'];

/** Impact page — defined metrics, honest "numbers arrive with the pilot".
 * Full version with live counters, MRV cycle, time-series charts, satellite map,
 * report download, and data transparency. */
export default function ImpactPage() {
  const { lang, t } = useLang();
  const c = impact[lang as 'fa' | 'en'];

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/impact" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />

      {/* live counters */}
      <LiveCounters />

      {/* metrics grid with 3D cards */}
      <section className="px-4 pb-10 sm:px-6">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <Reveal className="flex flex-col items-center text-center gap-4">
            <SectionHeading kicker={c.kicker} title={c.metricsTitle} lead={c.metricsNote} />
          </Reveal>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {c.metrics.map((metric, index) => (
              <Reveal key={metric.name} delay={index * 0.06}>
                <UniversalCard
                  title={metric.name}
                  desc={metric.desc}
                  unit={metric.unit}
                  icon="flask"
                  theme={METRIC_THEMES[index % METRIC_THEMES.length] as 'leaf' | 'aqua' | 'sand'}
                  index={index}
                  backContent={{
                    source: metric.source,
                    method: metric.method,
                    standard: metric.standard,
                    frequency: metric.frequency,
                    apiField: metric.apiField,
                  }}
                />
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* MRV cycle */}
      <MrvCycleChart />

      {/* time-series charts */}
      <ImpactTimeSeries />

      <RechartsImpactChart
        data={c.sampleTimeSeries}
      />

      {/* satellite map */}
      <SatelliteMap />

      {/* methodology */}
      <section className="px-4 pb-10 sm:px-6">
        <Reveal className="mx-auto max-w-4xl">
          <div className="glass rounded-3xl p-8">
            <h2 className="text-lg font-extrabold text-[var(--color-night-100)]">
              {c.methodTitle}
            </h2>
            <p className="mt-3 text-sm leading-8 text-[var(--color-night-200)]/65">
              {c.methodBody}
            </p>
          </div>
        </Reveal>
      </section>

      {/* report download */}
      <ImpactReportBox />

      {/* data provenance table */}
      <ImpactDataProvenance />

      {/* gallery + sample chart */}
      <section className="px-4 pb-10 sm:px-6" id="gallery">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <SectionHeading
            kicker={c.kicker}
            title={lang === 'fa' ? 'گالری میدان و پایش' : 'Field gallery & monitoring'}
            lead={
              lang === 'fa'
                ? 'تصویری از چیزی که پایش می‌کنیم: از اراضی حاشیه‌ای تا تالاب بازگردانده — و روند نمونهٔ شاخص پوشش گیاشتی.'
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
