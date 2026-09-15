import { useState } from 'react';

type ActivityType = 'data' | 'verify' | 'report' | 'status';

const typeColors: Record<ActivityType, string> = {
  data: 'bg-[var(--color-leaf-500)]/15 text-[var(--color-leaf-400)]',
  verify: 'bg-[var(--color-aqua-500)]/15 text-[var(--color-aqua-400)]',
  report: 'bg-[var(--color-sand-500)]/15 text-[var(--color-sand-400)]',
  status: 'bg-white/10 text-[var(--color-night-200)]/60',
};

interface Activity {
  id: string;
  text: string;
  time: string;
  type: ActivityType;
}

/** Real-time activity feed. */
export default function ActivityStream() {
  const [activities] = useState<Activity[]>([
    { id: '1', text: 'به‌روزرسانی داده‌های NDVI — مشهد', time: '12:30', type: 'data' },
    { id: '2', text: 'تأیید MRV — تالاب انزلی', time: '11:45', type: 'verify' },
    { id: '3', text: 'گزارش ماهانه منتشر شد', time: '10:15', type: 'report' },
    { id: '4', text: 'تغییر وضعیت پروژه — تبریز', time: '09:30', type: 'status' },
  ]);

  return (
    <div className="space-y-2">
      {activities.map((a) => (
        <div key={a.id} className="flex items-center gap-3 rounded-xl glass p-3 hover:bg-white/[0.06] transition-colors">
          <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${typeColors[a.type]}`}>
            {a.type.toUpperCase()}
          </span>
          <span className="flex-1 text-xs text-[var(--color-night-100)]/80">{a.text}</span>
          <span className="text-[10px] text-[var(--color-night-200)]/40">{a.time}</span>
        </div>
      ))}
    </div>
  );
}
