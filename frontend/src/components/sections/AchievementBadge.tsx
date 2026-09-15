import { cn } from '../../lib/utils';

/** Achievement/milestone badge display. */
export default function AchievementBadge({
  title,
  icon,
  earned = true,
}: {
  title: string;
  icon: string;
  earned?: boolean;
}) {
  return (
    <div
      className={cn(
        'rounded-2xl p-4 text-center transition-all duration-300 hover:scale-105',
        earned
          ? 'bg-gradient-to-br from-[var(--color-leaf-500)]/10 to-[var(--color-aqua-500)]/10 border border-[var(--color-leaf-500)]/20'
          : 'bg-white/3 border border-white/5 opacity-50 grayscale'
      )}
    >
      <span className="text-3xl" aria-hidden>{icon}</span>
      <p className="text-xs font-bold text-[var(--color-night-100)] mt-2">{title}</p>
      {earned && (
        <span className="inline-block mt-1 text-[10px] px-2 py-0.5 rounded-full bg-[var(--color-leaf-500)]/15 text-[var(--color-leaf-300)]">
          Earned
        </span>
      )}
    </div>
  );
}
