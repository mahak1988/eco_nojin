import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Lock, ArrowLeft } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface Props {
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  to: string;
  badge?: string;
}

export const ModuleCard: React.FC<Props> = ({ title, description, icon, color, to, badge }) => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const go = () => (user ? navigate(to) : navigate('/login', { state: { from: to } }));

  return (
    <motion.div
      onClick={go}
      whileHover={{ y: -10, scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className="card"
      style={{
        cursor: 'pointer',
        borderTop: `4px solid ${color}`,
        position: 'relative',
        overflow: 'hidden',
        padding: '1.75rem',
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(500px circle at 0% 0%, ${color}18, transparent 60%)`,
          pointerEvents: 'none',
        }}
      />
      {badge && (
        <span
          className="badge"
          style={{ position: 'absolute', top: 12, left: 12, background: color + '22', color }}
        >
          {badge}
        </span>
      )}

      <motion.div
        whileHover={{ rotate: 6, scale: 1.1 }}
        style={{
          width: 60,
          height: 60,
          borderRadius: 'var(--radius-xl)',
          background: color,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          marginBottom: '1.25rem',
          boxShadow: `0 8px 20px ${color}55`,
        }}
      >
        {icon}
      </motion.div>

      <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem' }}>{title}</h3>
      <p
        style={{
          color: 'var(--color-text-secondary)',
          fontSize: '0.9rem',
          lineHeight: 1.7,
          marginBottom: '1rem',
        }}
      >
        {description}
      </p>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          color,
          fontSize: '0.875rem',
          fontWeight: 600,
        }}
      >
        {!user && <Lock size={14} />}
        <span>{user ? 'باز کردن ماژول' : 'ورود برای دسترسی'}</span>
        <ArrowLeft size={14} className="animate-pulse" />
      </div>
    </motion.div>
  );
};
