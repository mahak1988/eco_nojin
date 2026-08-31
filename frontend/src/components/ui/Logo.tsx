import React from 'react';
import { motion } from 'framer-motion';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg';
  showSubtitle?: boolean;
}

export const Logo: React.FC<LogoProps> = ({ size = 'md', showSubtitle = true }) => {
  const sizes = {
    sm: { eco: '1.25rem', hydro: '1.25rem', sub: '0.625rem' },
    md: { eco: '1.5rem', hydro: '1.5rem', sub: '0.75rem' },
    lg: { eco: '2.5rem', hydro: '2.5rem', sub: '1rem' },
  };

  const currentSize = sizes[size];

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '0.25rem',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '1rem' }}>
        <motion.span
          className="logo-eco-nojin"
          style={{ fontSize: currentSize.eco }}
          whileHover={{ scale: 1.05 }}
          transition={{ type: 'spring', stiffness: 300 }}
        >
          Eco Nojin
        </motion.span>

        <motion.span
          style={{
            fontSize: currentSize.eco,
            color: 'var(--color-text-tertiary)',
            fontWeight: 300,
          }}
        >
          ×
        </motion.span>

        <motion.span
          className="logo-hydroma"
          style={{ fontSize: currentSize.hydro }}
          whileHover={{ scale: 1.05 }}
          transition={{ type: 'spring', stiffness: 300 }}
        >
          HyDroMa
        </motion.span>
      </div>

      {showSubtitle && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          style={{
            fontSize: currentSize.sub,
            color: 'var(--color-text-tertiary)',
            margin: 0,
            fontFamily: '"Vazirmatn", sans-serif',
            fontWeight: 400,
          }}
        >
          پلتفرم یکپارچه کشاورزی پایدار و مدیریت منابع آب
        </motion.p>
      )}
    </motion.div>
  );
};
