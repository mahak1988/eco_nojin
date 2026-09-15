import { useEffect, useRef } from 'react';

/** Animated gradient mesh background with floating orbs. */
export default function AnimatedMeshBackground() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const handleMouseMove = (e: MouseEvent) => {
      const x = (e.clientX / window.innerWidth) * 100;
      const y = (e.clientY / window.innerHeight) * 100;
      el.style.background = `
        radial-gradient(at ${x}% ${y}%, rgba(47,179,107,0.08) 0%, transparent 50%),
        radial-gradient(at ${100 - x}% ${100 - y}%, rgba(42,155,181,0.06) 0%, transparent 50%),
        var(--color-night-950)
      `;
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div
      ref={ref}
      className="fixed inset-0 -z-10 transition-all duration-500"
      style={{ background: 'var(--color-night-950)' }}
      aria-hidden
    />
  );
}
