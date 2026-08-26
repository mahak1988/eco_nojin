import React from 'react';
import { motion } from 'framer-motion';
import { LivingBackground } from '../../components/backgrounds/LivingBackground';
import { AnimatedLogo } from '../../components/branding/AnimatedLogo';

export const AuthShell: React.FC<{ children: React.ReactNode; title: string; subtitle: string }> = ({ children, title, subtitle }) => (
  <div style={{ minHeight: '100vh', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '4rem 1.5rem', overflow: 'hidden' }}>
    <LivingBackground showRain />
    <motion.div
      initial={{ opacity: 0, y: 40, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.6, type: 'spring', damping: 18 }}
      className="glass"
      style={{ position: 'relative', zIndex: 1, width: '100%', maxWidth: 460, borderRadius: 'var(--radius-2xl)', padding: '2.5rem', boxShadow: 'var(--shadow-2xl)' }}
    >
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <AnimatedLogo size="sm" showSubtitle={false} />
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, marginTop: '1.25rem', marginBottom: '0.5rem' }}>{title}</h1>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>{subtitle}</p>
      </div>
      {children}
    </motion.div>
  </div>
);

export const Field: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
  <motion.label initial={{ opacity: 0, x: -14 }} animate={{ opacity: 1, x: 0 }} style={{ display: 'block', marginBottom: '1.1rem' }}>
    <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 6, color: 'var(--color-text-secondary)' }}>{label}</span>
    {children}
  </motion.label>
);
