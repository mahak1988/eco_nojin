/** Export utilities — CSV and JSON download helpers. */

export function downloadJSON(data: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${filename}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function downloadCSV(data: Record<string, unknown>[], filename: string) {
  if (!data.length) return;

  const headers = Object.keys(data[0]);
  const csv = [
    headers.join(','),
    ...data.map((row) =>
      headers
        .map((header) => {
          const value = row[header];
          if (value === null || value === undefined) return '';
          const string = String(value);
          if (string.includes(',') || string.includes('"') || string.includes('\n')) {
            return `"${string.replace(/"/g, '""')}"`;
          }
          return string;
        })
        .join(','),
    ),
  ].join('\n');

  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${filename}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function exportHubRuns(runs: { id: string; model_id: string; title?: string | null; created_at?: string | null; shared: boolean }[], format: 'csv' | 'json') {
  const timestamp = new Date().toISOString().slice(0, 10);
  const baseName = `econojin-calculations-${timestamp}`;

  if (format === 'json') {
    downloadJSON(runs, baseName);
  } else {
    const csvData = runs.map((run) => ({
      id: run.id,
      model_id: run.model_id,
      title: run.title ?? '',
      created_at: run.created_at ?? '',
      shared: run.shared ? 'Yes' : 'No',
    }));
    downloadCSV(csvData, baseName);
  }
}
