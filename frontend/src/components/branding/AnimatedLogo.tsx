import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Leaf, Droplets } from 'lucide-react';

interface Props {
  size?: 'sm' | 'md' | 'lg';
  showSubtitle?: boolean;
}

/** لوگو: Eco Nojin -> خانه | HyDroMa -> داشبورد */
export const AnimatedLogo: React.FC<Props> = ({ size = 'md', showSubtitle = true }) => {
  const fs = size === 'lg' ? '2.5rem' : size === 'md' ? '1.5rem' : '1.2rem';
  const is = size === 'lg' ? 34 : size === 'md' ? 22 : 18;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', direction: 'ltr' }}>
        <Link
          to="/"
          style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 8 }}
          title="صفحه خانه"
        >
          <motion.span
            whileHover={{ scale: 1.15, rotate: -8 }}
            style={{ display: 'inline-flex', color: '#22c55e' }}
          >
            <Leaf size={is} className="animate-float" />
          </motion.span>
          <motion.span
            whileHover={{ scale: 1.06 }}
            className="logo-eco-nojin"
            style={{ fontSize: fs }}
          >
            Eco Nojin
          </motion.span>
        </Link>

        <span style={{ color: 'var(--color-text-tertiary)', fontWeight: 300 }}>×</span>

        <Link
          to="/hydroma"
          style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 8 }}
          title="داشبورد HyDroMa"
        >
          <motion.span
            whileHover={{ scale: 1.15, y: 3 }}
            style={{ display: 'inline-flex', color: '#3b82f6' }}
          >
            <Droplets size={is} className="animate-float-slow" />
          </motion.span>
          <motion.span
            whileHover={{ scale: 1.06 }}
            className="logo-hydroma"
            style={{ fontSize: fs }}
          >
            HyDroMa
          </motion.span>
        </Link>
      </div>
      {showSubtitle && (
        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-tertiary)', margin: 0 }}>
          پلتفرم یکپارچه کشاورزی پایدار و مدیریت هوشمند آب
        </p>
      )}
    </div>
  );
};
