import { Download, FileText, FileSpreadsheet, FileJson2 } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';

interface ReportFormat {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  format: 'csv' | 'json' | 'pdf';
  note: string;
}

/**
 * Impact report download box — CSV export via native Blob (no dependency),
 * PDF/JSON stubs marked for future implementation.
 */
export default function ImpactReportBox() {
  const { t, lang } = useLang();

  const formats: ReportFormat[] = [
    {
      label: lang === 'fa' ? 'CSV' : 'CSV',
      icon: FileSpreadsheet,
      format: 'csv',
      note: lang === 'fa' ? 'داده‌های خام متریک' : 'Raw metric data',
    },
    {
      label: lang === 'fa' ? 'JSON' : 'JSON',
      icon: FileJson2,
      format: 'json',
      note: lang === 'fa' ? 'داده‌های ساختاری' : 'Structured data',
    },
    {
      label: 'PDF',
      icon: FileText,
      format: 'pdf',
      note: lang === 'fa' ? 'خلاصه کارشناسی (بعد از پایلوت)' : 'Executive summary (after pilot)',
    },
  ];

  const downloadAs = (format: 'csv' | 'json' | 'pdf') => {
    const data = {
      exportedAt: new Date().toISOString(),
      lang,
      metrics: t.impact.metrics.map((m) => ({
        name: m.name,
        unit: m.unit,
        desc: m.desc,
        source: m.source,
        standard: m.standard,
      })),
      projects: t.impact.projects,
      timeSeries: t.impact.sampleTimeSeries,
    };

    if (format === 'csv') {
      const headers = ['name', 'unit', 'desc', 'source', 'standard'];
      const rows = data.metrics.map((m) =>
        headers.map((h) => `"${m[h as keyof typeof m] ?? ''}"`).join(','),
      );
      const csv = [headers.join(','), ...rows].join('\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `eco-nojin-impact-${lang}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } else if (format === 'json') {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `eco-nojin-impact-${lang}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } else if (format === 'pdf') {
      // PDF export is planned for Phase 2 (jsPDF dependency)
      alert(lang === 'fa' ? 'در دسترس پس از پایلوت' : 'Available after the pilot');
    }
  };

  return (
    <section className="px-4 py-12 sm:px-6">
      <Reveal className="mx-auto flex max-w-4xl flex-col gap-6">
        <div className="text-center">
          <h2 className="text-2xl font-extrabold text-[var(--color-night-100)] sm:text-3xl">
            {t.impact.reportTitle}
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-[var(--color-night-200)]/60">
            {t.impact.reportNote}
          </p>
        </div>

        <div className="glass rounded-3xl p-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:gap-4">
            {formats.map((fmt) => {
              const Icon = fmt.icon;
              return (
                <button
                  key={fmt.format}
                  type="button"
                  onClick={() => downloadAs(fmt.format)}
                  className="glass glass-hover flex flex-1 items-center justify-center gap-2 rounded-2xl py-4 text-center transition-all"
                >
                  <Icon className="h-5 w-5 text-[var(--color-aqua-500)]" />
                  <span className="text-sm font-bold text-[var(--color-night-100)]">
                    {fmt.label}
                  </span>
                  <span className="mt-1 text-[10px] text-[var(--color-night-200)]/40">
                    {fmt.note}
                  </span>
                </button>
              );
            })}
          </div>

          <p className="mt-4 flex items-center gap-1 text-[10px] text-[var(--color-night-200)]/35">
            <Download className="h-3 w-3" />
            {lang === 'fa'
              ? 'خروجی شامل تمام متریک‌ها، پروژه‌ها و داده‌های نمونه است؛ با آغاز پایلوت به‌روزرسانی می‌شود.'
              : 'Export includes all metrics, projects, and sample data; updated with the pilot launch.'}
          </p>
        </div>
      </Reveal>
    </section>
  );
}
