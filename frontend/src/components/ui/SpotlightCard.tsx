/** SpotlightCard — mouse-following radial glow on any card surface.
 * The glow is a motion.div driven by spring-smoothed cursor position;
 * it only appears on hover and never blocks interaction. */

import { useRef, type ReactNode } from 'react';
import { motion, useMotionTemplate, useMotionValue, useSpring, useReducedMotion } from 'framer-motion';

interface SpotlightCardProps {
  children: ReactNode;
  className?: string;
  /** Glow radius in px. */
  radius?: number;
  /** Glow tint (rgba). Defaults to the leaf accent. */
  tint?: string;
}

export default function SpotlightCard({
  children,
  className = '',
  radius = 240,
  tint = 'rgba(134, 226, 172, 0.10)',
}: SpotlightCardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const reduceMotion = useReducedMotion();
  const mx = useMotionValue(-9999);
  const my = useMotionValue(-9999);
  const sx = useSpring(mx, { stiffness: 260, damping: 30 });
  const sy = useSpring(my, { stiffness: 260, damping: 30 });
  const glow = useMotionTemplate`radial-gradient(${radius}px circle at ${sx}px ${sy}px, ${tint}, transparent 68%)`;

  return (
    <motion.div
      ref={ref}
      onMouseMove={(event) => {
        const rect = ref.current?.getBoundingClientRect();
        if (!rect) return;
        mx.set(event.clientX - rect.left);
        my.set(event.clientY - rect.top);
      }}
      onMouseLeave={() => {
        mx.set(-9999);
        my.set(-9999);
      }}
      className={`group relative overflow-hidden ${className}`}
    >
      {reduceMotion ? null : (
        <motion.div
          aria-hidden
          className="pointer-events-none absolute inset-0 z-[1] opacity-0 transition-opacity duration-300 group-hover:opacity-100"
          style={{ background: glow }}
        />
      )}
      {children}
    </motion.div>
  );
}
