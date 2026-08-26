import React from 'react';
import { motion } from 'framer-motion';
import { Droplets, Leaf, Zap, ArrowRight } from 'lucide-react';
import { PublicLayout } from '../components/layout/PublicLayout';
import { Card, Button } from '../components/ui';

export const HydromaPage: React.FC = () => {
  const features = [
    {
      icon: <Droplets size={32} />,
      title: 'مدیریت هوشمند آب',
      description: 'الگوریتم‌های ET-based برای بهینه‌سازی مصرف آب تا ۴۰٪',
      color: '#3b82f6',
    },
    {
      icon: <Leaf size={32} />,
      title: 'پایش سلامت خاک',
      description: 'تحلیل رطوبت، دما، و مواد مغذی با سنسورهای IoT',
      color: '#10b981',
    },
    {
      icon: <Zap size={32} />,
      title: 'پیش‌بینی با AI',
      description: 'مدل‌های یادگیری ماشین برای تخمین دقیق عملکرد',
      color: '#f59e0b',
    },
  ];

  return (
    <PublicLayout>
      <section style={{ padding: '6rem 2rem', maxWidth: 1400, margin: '0 auto' }}>
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ textAlign: 'center', marginBottom: '4rem' }}
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', delay: 0.2 }}
            style={{
              display: 'inline-block',
              fontSize: '4rem',
              marginBottom: '1rem',
            }}
          >
            💧
          </motion.div>
          <h1 style={{ fontSize: '3rem', fontWeight: 700, marginBottom: '1rem' }}>
            <span className="logo-hydroma">HyDroMa</span>
          </h1>
          <p style={{ fontSize: '1.25rem', color: 'var(--color-text-secondary)', maxWidth: 700, margin: '0 auto' }}>
            Hydrological Dynamic Model - سیستم یکپارچه مدیریت منابع آب و خاک
          </p>
        </motion.div>

        {/* Features */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '2rem',
            marginBottom: '4rem',
          }}
        >
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ y: -8 }}
              className="card"
              style={{ padding: '2rem', cursor: 'pointer' }}
            >
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: 'var(--radius-xl)',
                  background: `${feature.color}20`,
                  color: feature.color,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '1.5rem',
                }}
              >
                {feature.icon}
              </div>
              <h3 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '0.75rem' }}>
                {feature.title}
              </h3>
              <p style={{ color: 'var(--color-text-secondary)', lineHeight: 1.7, margin: 0 }}>
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Integration with Eco Nojin */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="card"
          style={{ padding: '3rem', textAlign: 'center' }}
        >
          <h2 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '1.5rem' }}>
            یکپارچه‌سازی با Eco Nojin
          </h2>
          <p style={{ fontSize: '1.125rem', color: 'var(--color-text-secondary)', maxWidth: 800, margin: '0 auto 2rem' }}>
            HyDroMa و Eco Nojin با هم کار می‌کنند تا یک اکوسیستم کامل برای کشاورزی پایدار ایجاد کنند.
            از شبیه‌سازی دقیق تا مدیریت هوشمند و فروش محصول.
          </p>
          
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '2rem', marginBottom: '2rem' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🌱</div>
              <div className="logo-eco-nojin">Eco Nojin</div>
            </div>
            <ArrowRight size={32} color="var(--color-primary)" />
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>💧</div>
              <div className="logo-hydroma">HyDroMa</div>
            </div>
          </div>

          <Button variant="primary" size="lg">
            شروع استفاده از HyDroMa
          </Button>
        </motion.div>
      </section>
    </PublicLayout>
  );
};
