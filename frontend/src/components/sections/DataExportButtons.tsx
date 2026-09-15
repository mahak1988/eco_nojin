import { useLang } from '../../i18n/LanguageContext';

/** Export data buttons (CSV/JSON/PDF). */
export default function DataExportButtons({
  data,
}: {
  data?: Record<string, unknown>[];
}) {
  const { lang } = useLang();

  const exportCSV = () => {
    const headers = ['name', 'value'];
    const rows = (data || [{ name: 'مشهد', value: 2400 }, { name: 'تبریز', value: 1600 }])
      .map((r) => headers.map((h) => String((r as Record<string, unknown>)[h] ?? '')).join(','))
      .join('\n');
    const blob = new Blob([[headers.join(','), rows].join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `eco-nojin-export-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify(data || { projects: 'sample' }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `eco-nojin-export-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex gap-2">
      <button
        type="button"
        onClick={exportCSV}
        className="rounded-xl glass glass-hover px-4 py-2 text-xs font-bold text-[var(--color-night-100)] hover:text-[var(--color-leaf-300)]"
      >
        {lang === 'fa' ? '📄 CSV' : '📄 CSV'}
      </button>
      <button
        type="button"
        onClick={exportJSON}
        className="rounded-xl glass glass-hover px-4 py-2 text-xs font-bold text-[var(--color-night-100)] hover:text-[var(--color-aqua-300)]"
      >
        {lang === 'fa' ? '📋 JSON' : '📋 JSON'}
      </button>
    </div>
  );
}
