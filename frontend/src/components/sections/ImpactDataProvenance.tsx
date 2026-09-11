import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';
import SectionHeading from '../ui/SectionHeading';

/**
 * Data transparency table — shows source, method, standard, and frequency
 * for every impact metric. FAIR Data Principles compliant by design.
 */
export default function ImpactDataProvenance() {
  const { t, lang } = useLang();

  const headers = {
    metric: lang === 'fa' ? 'متریک' : 'Metric',
    source: lang === 'fa' ? 'منبع' : 'Source',
    method: lang === 'fa' ? 'روش' : 'Method',
    standard: lang === 'fa' ? 'استاندارد' : 'Standard',
    frequency: lang === 'fa' ? 'فرکانس' : 'Frequency',
  };

  return (
    <section className="px-4 py-12 sm:px-6">
      <Reveal className="mx-auto flex max-w-6xl flex-col gap-8">
        <SectionHeading
          kicker={t.impact.kicker}
          title={t.impact.transparencyTitle}
          lead={t.impact.transparencyNote}
        />

        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr>
                <th className="text-start text-xs font-extrabold uppercase text-[var(--color-night-200)]/40">
                  {headers.metric}
                </th>
                <th className="text-start text-xs font-extrabold uppercase text-[var(--color-night-200)]/40">
                  {headers.source}
                </th>
                <th className="text-start text-xs font-extrabold uppercase text-[var(--color-night-200)]/40">
                  {headers.method}
                </th>
                <th className="hidden text-start text-xs font-extrabold uppercase text-[var(--color-night-200)]/40 md:table-cell">
                  {headers.standard}
                </th>
                <th className="text-start text-xs font-extrabold uppercase text-[var(--color-night-200)]/40">
                  {headers.frequency}
                </th>
              </tr>
            </thead>
            <tbody>
              {t.impact.metrics.map((metric, index) => (
                <Reveal key={metric.name} delay={index * 0.04}>
                  <tr className="border-b border-white/5">
                    <td className="py-3 text-sm font-bold text-[var(--color-night-100)]">
                      {metric.name}
                    </td>
                    <td className="py-3 text-xs text-[var(--color-night-200)]/60">
                      {metric.source || '-'}
                    </td>
                    <td className="py-3 text-xs text-[var(--color-night-200)]/60">
                      {metric.method || '-'}
                    </td>
                    <td className="hidden py-3 text-xs text-[var(--color-aqua-300)]/70 md:table-cell">
                      {metric.standard || '-'}
                    </td>
                    <td className="py-3 text-xs text-[var(--color-sand-300)]/60">
                      {metric.frequency || '-'}
                    </td>
                  </tr>
                </Reveal>
              ))}
            </tbody>
          </table>

          <p className="mt-5 text-center text-[10px] text-[var(--color-night-200)]/35">
            {t.impact.transparencyNote}
          </p>
        </div>
      </Reveal>
    </section>
  );
}
