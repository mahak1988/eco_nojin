/** Loading skeleton — matches BaseCard layout for seamless placeholders. */

interface SkeletonProps {
  className?: string;
  title?: boolean;
  lines?: number;
}

export default function Skeleton({ className = '', title = false, lines = 3 }: SkeletonProps) {
  return (
    <div className={`glass flex flex-col gap-[var(--spacing-md)] rounded-[var(--radius-2xl)] p-[var(--spacing-xl)] ${className}`}>
      {title && <div className="skeleton skeleton-title" />}
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="skeleton skeleton-text"
          style={{ width: `${100 - i * 15}%` }}
        />
      ))}
    </div>
  );
}
