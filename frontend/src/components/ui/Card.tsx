import React from 'react';
import { motion } from 'framer-motion';

interface CardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  icon?: React.ReactNode;
  className?: string;
  hover?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  icon,
  className = '',
  hover = true }) => {
  return (
    <motion.div
      className={`card ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={hover ? { y: -4, boxShadow: 'var(--shadow-lg)' } : {}}
      transition={{ duration: 0.3 }}
    >
      {(title || icon) && (
        <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
          {icon && (
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 'var(--radius-lg)',
                background: 'var(--color-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                flexShrink: 0 }}
            >
              {icon}
            </div>
          )}
          <div style={{ flex: 1 }}>
            {title && (
              <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 600 }}>
                {title}
              </h3>
            )}
            {subtitle && (
              <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem', color: 'var(--color-text-tertiary)' }}>
                {subtitle}
              </p>
            )}
          </div>
        </div>
      )}
      {children}
    </motion.div>
  );
};
