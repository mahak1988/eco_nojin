import { cn } from '../../lib/utils';

/** Geographic heatmap grid. */
export default function HeatmapGrid({
  data,
}: {
  data?: { region: string; value: number; color?: string }[];
}) {
  const defaultData = [
    { region: 'تهران', value: 85 },
    { region: 'مشهد', value: 62 },
    { region: 'اصفهان', value: 71 },
    { region: 'شیراز', value: 45 },
    { region: 'تبریز', value: 58 },
    { region: 'رشت', value: 78 },
    { region: 'اهواز', value: 33 },
    { region: 'کرمان', value: 52 },
  ];

  const items = data || defaultData;

  const getColor = (val: number) => {
    if (val >= 75) return 'bg-[var(--color-leaf-500)]/60';
    if (val >= 50) return 'bg-[var(--color-leaf-500)]/35';
    if (val >= 30) return 'bg-[var(--color-sand-500)]/30';
    return 'bg-[var(--color-sand-500)]/15';
  };

  return (
    <div className="grid grid-cols-4 gap-2">
      {items.map((item) => (
        <div
          key={item.region}
          className={cn('rounded-xl p-3 text-center transition-all duration-300 hover:scale-105 cursor-pointer', getColor(item.value))}
          title={`${item.region}: ${item.value}%`}
        >
          <p className="text-[10px] font-bold text-[var(--color-night-100)]">{item.region}</p>
          <p className="text-lg font-extrabold text-[var(--color-leaf-300)]">{item.value}%</p>
        </div>
      ))}
    </div>
  );
}
