import type { ReactNode } from 'react';
import { cn } from './cn';

export interface DataGridColumn<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
}

export function DataGrid<T>({
  caption,
  columns,
  rows,
  rowKey,
  className,
}: {
  caption: string;
  columns: DataGridColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  className?: string;
}) {
  return (
    <div className={cn('overflow-x-auto rounded-lg border border-line', className)}>
      <table className="w-full min-w-40 border-collapse text-start text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead className="bg-surface-2">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className="px-4 py-3 text-start font-semibold text-ink"
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={rowKey(row)} className="border-t border-line">
              {columns.map((column) => (
                <td key={column.key} className="px-4 py-3 text-ink">
                  {column.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
