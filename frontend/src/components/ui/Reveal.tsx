import { motion, useReducedMotion } from 'framer-motion';
import type { ReactNode } from 'react';

interface RevealProps {
  children: ReactNode;
  className?: string;
  delay?: number;
  y?: number;
  onClick?: (e: React.MouseEvent<HTMLDivElement>) => void;
}

/**
 * Scroll-triggered entrance wrapper. Respects prefers-reduced-motion by
 * rendering children without animation.
 */
export default function Reveal({ children, className, delay = 0, y = 26, onClick }: RevealProps) {
  const reduceMotion = useReducedMotion();

  if (reduceMotion) {
    return <div className={className} onClick={onClick}>{children}</div>;
  }

  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-70px' }}
      transition={{ duration: 0.65, delay, ease: [0.22, 0.61, 0.36, 1] }}
      onClick={onClick}
    >
      {children}
    </motion.div>
  );
}
