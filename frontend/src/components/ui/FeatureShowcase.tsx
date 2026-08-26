import React from 'react';
import { motion } from 'framer-motion';

interface Feature {
  icon: React.ReactNode;
  title: string;
  description: string;
  color: string;
}

interface FeatureShowcaseProps {
  features: Feature[];
  title?: string;
  subtitle?: string;
}

/**
 * نمایش ویژگی‌ها با کارت‌های زیبا
 */
export const FeatureShowcase: React.FC<FeatureShowcaseProps> = ({
  features,
  title,
  subtitle,
}) => {
  return (
    <div>
      {(title || subtitle) && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          style={{ textAlign: 'center', marginBottom: '3rem' }}
        >
          {title && (
            <h2 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '0.75rem' }}>
              {title}
            </h2>
          )}
          {subtitle && (
            <p style={{ fontSize: '1.125rem', color: 'var(--color-text-secondary)', maxWidth: 600, margin: '0 auto' }}>
              {subtitle}
            </p>
          )}
        </motion.div>
      )}

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '1.5rem',
      }}>
        {features.map((feature, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ y: -8, boxShadow: 'var(--shadow-xl)' }}
            className="card"
            style={{ padding: '2rem', cursor: 'pointer' }}
          >
            <div style={{
              width: 56,
              height: 56,
              borderRadius: 'var(--radius-xl)',
              background: `${feature.color}20`,
              color: feature.color,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1.5rem',
            }}>
              {feature.icon}
            </div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.75rem' }}>
              {feature.title}
            </h3>
            <p style={{ color: 'var(--color-text-secondary)', lineHeight: 1.7, margin: 0 }}>
              {feature.description}
            </p>
          </motion.div>
        ))}
      </div>
    </div>
  );
};
