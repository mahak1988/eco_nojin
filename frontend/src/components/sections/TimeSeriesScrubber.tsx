import { useState } from 'react';

/** Interactive time-series scrubber. */
export default function TimeSeriesScrubber({
  data,
}: {
  data?: { label: string; value: number }[];
}) {
  const defaultData = [
    { label: 'فروردین', value: 200 }, { label: 'اردیبهشت', value: 350 },
    { label: 'خرداد', value: 280 }, { label: 'تیر', value: 420 },
    { label: 'مرداد', value: 380 }, { label: 'شهریور', value: 500 },
  ];
  const items = data || defaultData;
  const [selected, setSelected] = useState(0);
  const current = items[selected];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-bold text-[var(--color-night-100)]">{current.label}</span>
        <span className="text-2xl font-extrabold text-[var(--color-leaf-300)]">{current.value}</span>
      </div>
      <input
        type="range"
        min="0"
        max={items.length - 1}
        value={selected}
        onChange={(e) => setSelected(parseInt(e.target.value))}
        className="w-full accent-[var(--color-leaf-500)]"
        aria-label="زمان"
      />
      <div className="flex justify-between">
        {items.map((item, i) => (
          <button
            key={item.label}
            type="button"
            onClick={() => setSelected(i)}
            className={`text-[10px] px-1 rounded ${i === selected ? 'bg-[var(--color-leaf-500)]/20 text-[var(--color-leaf-300)]' : 'text-[var(--color-night-200)]/40'}`}
          >
            {item.label[0]}
          </button>
        ))}
      </div>
    </div>
  );
}
