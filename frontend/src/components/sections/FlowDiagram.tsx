/** Animated flow/sankey diagram. */
export default function FlowDiagram({
  nodes,
}: {
  nodes?: { from: string; to: string; value: number }[];
}) {
  const defaultNodes = [
    { from: 'مبذی', to: 'تأثیر زیست‌محیطی', value: 100 },
    { from: 'مبذی', to: 'تأثیر اجتماعی', value: 60 },
    { from: 'مبذی', to: 'تأثیر اقتصادی', value: 40 },
    { from: 'تأثیر زیست‌محیطی', to: 'کاهش CO₂', value: 70 },
    { from: 'تأثیر زیست‌محیطی', to: 'بازسازی جنگل', value: 55 },
    { from: 'تأثیر اجتماعی', to: 'اشتغال', value: 45 },
    { from: 'تأثیر اقتصادی', to: 'درآمد', value: 35 },
  ];

  const items = nodes || defaultNodes;
  const maxVal = Math.max(...items.map((n) => n.value));

  return (
    <div className="flex flex-col gap-4" dir="ltr">
      {items.map((item, i) => (
        <div key={i} className="flex items-center gap-3">
          <span className="text-xs text-[var(--color-night-200)]/60 w-24 text-right">{item.from}</span>
          <div className="flex-1 h-3 rounded-full bg-white/5 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-[var(--color-leaf-500)] to-[var(--color-aqua-400)] transition-all duration-1000"
              style={{ width: `${(item.value / maxVal) * 100}%` }}
            />
          </div>
          <span className="text-xs font-bold text-[var(--color-leaf-300)] w-8">{item.value}%</span>
          <span className="text-xs text-[var(--color-night-200)]/40">→</span>
          <span className="text-xs text-[var(--color-night-200)]/60 w-24">{item.to}</span>
        </div>
      ))}
    </div>
  );
}
