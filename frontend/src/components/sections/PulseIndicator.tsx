import { useEffect, useState } from 'react';

/** Live pulse indicator with status. */
export default function PulseIndicator({
  label,
  active = true,
}: {
  label?: string;
  active?: boolean;
}) {
  const [pulse, setPulse] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => setPulse((p) => !p), 2000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="flex items-center gap-2">
      <span
        className="h-2.5 w-2.5 rounded-full transition-colors duration-500"
        style={{
          backgroundColor: active ? 'var(--color-leaf-500)' : 'var(--color-sand-500)',
          boxShadow: pulse && active ? '0 0 8px var(--color-leaf-500)' : 'none',
        }}
        aria-hidden
      />
      {label && <span className="text-xs text-[var(--color-night-200)]/60">{label}</span>}
    </div>
  );
}
