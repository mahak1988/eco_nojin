import { useState } from 'react';

/** Expandable panel showing full data when triggered. */
export default function ChartDetailPanel({
  title,
  data,
}: {
  title: string;
  data: { label: string; value: number }[];
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-3xl glass p-4">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full text-left"
      >
        <h3 className="text-sm font-bold text-[var(--color-night-100)]">{title}</h3>
        <span className="text-xs text-[var(--color-leaf-300)]">{open ? '▼' : '▶'}</span>
      </button>
      {open && (
        <div className="mt-4 space-y-2">
          {data.map((d) => (
            <div key={d.label} className="flex items-center justify-between text-xs">
              <span className="text-[var(--color-night-200)]/60">{d.label}</span>
              <span className="font-bold text-[var(--color-leaf-300)]">{d.value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
