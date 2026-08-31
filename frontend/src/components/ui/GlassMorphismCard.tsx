import React from 'react';
import { motion } from 'framer-motion';

interface GlassMorphismCardProps {
  children: React.ReactNode;
  title?: string;
  icon?: React.ReactNode;
  gradient?: string;
  className?: string;
}

/**
 * کارت شیشه‌ای مدرن با افکت Glass Morphism
 */
export const GlassMorphismCard: React.FC<GlassMorphismCardProps> = ({
  children,
  title,
  icon,
  gradient = 'linear-gradient(135deg, var(--color-primary), var(--color-info))',
  className = '',
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.02, y: -4 }}
      className={className}
      style={{
        background: 'var(--color-surface)',
        backdropFilter: 'blur(20px)',
        borderRadius: 'var(--radius-2xl)',
        border: '1px solid var(--color-border)',
        padding: '2rem',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Gradient Orb */}
      <div
        style={{
          position: 'absolute',
          top: -50,
          right: -50,
          width: 200,
          height: 200,
          borderRadius: '50%',
          background: gradient,
          opacity: 0.1,
          filter: 'blur(40px)',
        }}
      />

      {(title || icon) && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            marginBottom: '1.5rem',
            position: 'relative',
            zIndex: 1,
          }}
        >
          {icon && (
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: 'var(--radius-xl)',
                background: gradient,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
              }}
            >
              {icon}
            </div>
          )}
          {title && <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 600 }}>{title}</h3>}
        </div>
      )}

      <div style={{ position: 'relative', zIndex: 1 }}>{children}</div>
    </motion.div>
  );
};
