import React from 'react';
import { motion } from 'framer-motion';
import { PublicLayout } from '../components/layout/PublicLayout';
import {
  Leaf, Droplets, Wind, TrendingUp, Brain, Satellite,
  BarChart3, Shield, Zap, Users, Globe, Database } from 'lucide-react';

const featureCategories = [
  {
    title: 'مدیریت آب و خاک',
    features: [
      { icon: Droplets, title: 'آبیاری هوشمند', description: 'الگوریتم‌های ET-based برای بهینه‌سازی مصرف آب' },
      { icon: Leaf, title: 'تحلیل خاک', description: 'پایش رطوبت، دما، و مواد مغذی خاک' },
      { icon: Wind, title: 'بادشکن و فرسایش', description: 'طراحی سیستم‌های حفاظتی و کاهش فرسایش' },
    ] },
  {
    title: 'هوش مصنوعی و شبیه‌سازی',
    features: [
      { icon: Brain, title: 'پیش‌بینی عملکرد', description: 'مدل‌های ML برای تخمین دقیق محصول' },
      { icon: Satellite, title: 'تحلیل ماهواره‌ای', description: 'NDVI و شاخص‌های سلامت گیاه' },
      { icon: Zap, title: 'شبیه‌ساز سه‌بعدی', description: 'نمایش تعاملی مزرعه در فضای ۳D' },
    ] },
  {
    title: 'اقتصاد و بازار',
    features: [
      { icon: BarChart3, title: 'تحلیل سودآوری', description: 'محاسبه ROI و بهینه‌سازی هزینه‌ها' },
      { icon: Users, title: 'بازار محلی', description: 'اتصال مستقیم به خریداران' },
      { icon: Globe, title: 'اعتبار کربن', description: 'کسب درآمد از طریق Carbon Credits' },
    ] },
];

export const FeaturesPage: React.FC = () => {
  return (
    <PublicLayout>
      <section style={{ padding: '6rem 2rem', maxWidth: 1400, margin: '0 auto' }}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ textAlign: 'center', marginBottom: '5rem' }}
        >
          <h1 style={{ fontSize: '3rem', fontWeight: 700, marginBottom: '1.5rem' }}>
            ویژگی‌ها و قابلیت‌ها
          </h1>
          <p style={{ fontSize: '1.25rem', color: 'var(--color-text-secondary)', maxWidth: 700, margin: '0 auto' }}>
            مجموعه کاملی از ابزارها برای مدیریت هوشمند و پایدار مزرعه شما
          </p>
        </motion.div>

        {featureCategories.map((category, catIndex) => (
          <motion.div
            key={catIndex}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            style={{ marginBottom: '4rem' }}
          >
            <h2 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '2rem', textAlign: 'center' }}>
              {category.title}
            </h2>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                gap: '2rem' }}
            >
              {category.features.map((feature, index) => {
                const Icon = feature.icon;
                return (
                  <motion.div
                    key={index}
                    whileHover={{ y: -8, boxShadow: 'var(--shadow-xl)' }}
                    className="card"
                    style={{ padding: '2rem', cursor: 'pointer' }}
                  >
                    <div
                      style={{
                        width: 64,
                        height: 64,
                        borderRadius: 'var(--radius-xl)',
                        background: 'linear-gradient(135deg, var(--color-primary), var(--color-accent))',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        marginBottom: '1.5rem' }}
                    >
                      <Icon size={32} />
                    </div>
                    <h3 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '0.75rem' }}>
                      {feature.title}
                    </h3>
                    <p style={{ color: 'var(--color-text-secondary)', lineHeight: 1.7, margin: 0 }}>
                      {feature.description}
                    </p>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        ))}
      </section>
    </PublicLayout>
  );
};
