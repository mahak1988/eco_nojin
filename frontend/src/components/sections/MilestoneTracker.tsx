import { useEffect, useState } from 'react';

/** Real-time milestone tracker with progress animation. */
export default function MilestoneTracker() {
  const milestones = [
    { date: '۱۴۰۱/۰۱', title: 'تأسیس', description: '', progress: 100, achieved: true },
    { date: '۱۴۰۲/۰۳', title: 'پروژه پایلوت', description: '', progress: 100, achieved: true },
    { date: '۱۴۰۳/۰۶', title: 'مقیاس‌پذیری', description: '', progress: 88, achieved: false },
    { date: '۱۴۰۴/۰۹', title: 'مدل سه‌بعدی', description: '', progress: 65, achieved: false },
  ];

  const [progress, setProgress] = useState(milestones.map((m) => m.progress));

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prev) => prev.map((p) => (p < 100 ? Math.min(p + 1, 100) : p)));
    }, 3000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="space-y-4">
      {milestones.map((m, i) => (
        <div key={m.title} className="rounded-2xl glass p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-bold text-[var(--color-night-100)]">{m.title}</span>
            <span className="text-xs text-[var(--color-night-200)]/50">{m.date}</span>
          </div>
          <div className="h-2 rounded-full bg-white/5 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-[var(--color-leaf-500)] to-[var(--color-aqua-400)] transition-all duration-1000"
              style={{ width: `${progress[i]}%` }}
            />
          </div>
          <p className="text-[10px] text-[var(--color-night-200)]/40 mt-1">{progress[i]}%</p>
        </div>
      ))}
    </div>
  );
}
