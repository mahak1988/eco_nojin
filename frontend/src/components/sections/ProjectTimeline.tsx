import { useState } from 'react';
import { cn } from '../../lib/utils';
import { MILESTONES_DATA } from '../../data/homeData';

/** Interactive project milestone timeline. */
export default function ProjectTimeline() {
  const [active, setActive] = useState(MILESTONES_DATA.length - 1);

  return (
    <div className="relative" dir="rtl">
      <div className="absolute right-0 top-0 bottom-0 w-0.5 bg-white/10" aria-hidden />
      <div className="space-y-4">
        {MILESTONES_DATA.map((m, i) => (
          <button
            key={m.date}
            type="button"
            onClick={() => setActive(i)}
            className={cn(
              'relative flex items-center gap-4 text-right transition-all duration-300 w-full',
              active === i ? 'opacity-100' : 'opacity-50 hover:opacity-80'
            )}
          >
            <div
              className={cn(
                'absolute right-[-5px] h-3 w-3 rounded-full border-2',
                m.achieved
                  ? 'bg-[var(--color-leaf-500)] border-[var(--color-leaf-500)]'
                  : 'bg-[var(--color-night-800)] border-[var(--color-sand-500)]'
              )}
              aria-hidden
            />
            <div className="flex-1 rounded-2xl glass p-4">
              <p className="text-[10px] text-[var(--color-night-200)]/50">{m.date}</p>
              <p className="text-sm font-bold text-[var(--color-night-100)]">{m.title}</p>
              {active === i && <p className="text-xs text-[var(--color-night-200)]/60 mt-1">{m.description}</p>}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
