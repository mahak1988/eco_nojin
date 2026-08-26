import React from 'react';
import { motion } from 'framer-motion';
import {
  Sprout, Droplets, Wind, Beef, Leaf, Map, Store, Compass,
  BarChart3, Satellite, TrendingUp, Users, Globe, Zap } from 'lucide-react';
import { PublicLayout } from '../components/layout/PublicLayout';
import { LivingBackground } from '../components/backgrounds/LivingBackground';
import { AnimatedLogo } from '../components/branding/AnimatedLogo';
import { ModuleCard } from '../components/ui/ModuleCard';
import { Button } from '../components/ui/Button';

const modules = [
  { title: 'برنامه کشت', description: 'شبیه‌سازی رشد محصول و مقایسه سناریوهای کشت چندلایه', icon: <Sprout size={28} />, color: '#22c55e', to: '/simulator' },
  { title: 'مدیریت آب', description: 'بودجه آب، نفوذپذیری، رواناب و تغذیه آبخوان', icon: <Droplets size={28} />, color: '#3b82f6', to: '/simulator' },
  { title: 'باد و فرسایش', description: 'تحلیل فرسایش بادی/آبی و طراحی بادشکن', icon: <Wind size={28} />, color: '#f59e0b', to: '/simulator' },
  { title: 'دامداری', description: 'شبیه‌ساز گاو، گوسفند، بز و طیور + اقتصاد گله', icon: <Beef size={28} />, color: '#b45309', to: '/simulator' },
  { title: 'کربن و اعتبار', description: 'پیش‌بینی ترشح کربن و صدور اعتبار کربن', icon: <Leaf size={28} />, color: '#10b981', to: '/simulator' },
  { title: 'نقشه و زمین', description: 'نمای سه‌بعدی مزرعه و تحلیل زمین', icon: <Map size={28} />, color: '#8b5cf6', to: '/simulator' },
  { title: 'بازارچه محلی', description: 'فروش مستقیم محصول بدون واسطه', icon: <Store size={28} />, color: '#eab308', to: '/simulator' },
  { title: 'گردشگری بوم‌گردی', description: 'تورهای روستایی و درآمد پایدار', icon: <Compass size={28} />, color: '#06b6d4', to: '/simulator' },
  { title: 'گزارش‌ها', description: 'تحلیل سودآوری و گزارش پایداری', icon: <BarChart3 size={28} />, color: '#6366f1', to: '/simulator' },
  { title: 'پایش ماهواره‌ای', description: 'NDVI و سلامت گیاه از فضا', icon: <Satellite size={28} />, color: '#0ea5e9', to: '/simulator' },
];

const stats = [
  { value: '۵۰۰+', label: 'مزرعه فعال', icon: Users },
  { value: '۴۰٪', label: 'کاهش مصرف آب', icon: Droplets },
  { value: '۴۵٪', label: 'افزایش عملکرد', icon: TrendingUp },
  { value: '۱۲', label: 'کشور', icon: Globe },
];

export const HomePage: React.FC = () => {
  return (
    <PublicLayout>
      {/* HERO زنده */}
      <section style={{ position: 'relative', minHeight: '92vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '6rem 2rem 8rem', overflow: 'hidden' }}>
        <LivingBackground />
        <div style={{ position: 'relative', zIndex: 1, textAlign: 'center', maxWidth: 1000 }}>
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}>
            <AnimatedLogo size="lg" />
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2, duration: 0.7 }}
            style={{ fontSize: 'clamp(2.2rem, 5.5vw, 3.8rem)', fontWeight: 800, margin: '2.5rem 0 1.25rem', lineHeight: 1.25 }}
          >
            آینده کشاورزی،
            <span className="gradient-text"> پایدار و هوشمند</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35, duration: 0.7 }}
            style={{ fontSize: '1.2rem', color: 'var(--color-text-secondary)', maxWidth: 720, margin: '0 auto 2.5rem', lineHeight: 1.9 }}
          >
            از قطره تا اقیانوس، از دانه تا جنگل.
            <br />
            با شبیه‌سازهای علمی و داده ماهواره‌ای، مزرعه‌ات را مانند یک اکوسیستم زنده مدیریت کن.
          </motion.p>

          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5, duration: 0.7 }}
            style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button variant="primary" size="lg" icon={<Zap size={18} className="animate-pulse" />}>شروع رایگان</Button>
            <Button variant="secondary" size="lg">مشاهده دمو</Button>
          </motion.div>
        </div>
      </section>

      {/* Stats */}
      <section style={{ padding: '4rem 2rem', background: 'var(--color-surface)' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '2rem' }}>
          {stats.map((s, i) => {
            const Icon = s.icon;
            return (
              <motion.div key={i} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }} style={{ textAlign: 'center' }}>
                <motion.div whileHover={{ scale: 1.15, rotate: 8 }} style={{ display: 'inline-flex', color: 'var(--color-primary)', marginBottom: '0.75rem' }}>
                  <Icon size={34} className="animate-float" />
                </motion.div>
                <div style={{ fontSize: '2.4rem', fontWeight: 800 }}>{s.value}</div>
                <div style={{ color: 'var(--color-text-secondary)' }}>{s.label}</div>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* Module cards */}
      <section style={{ padding: '6rem 2rem' }}>
        <div style={{ maxWidth: 1400, margin: '0 auto' }}>
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
            <h2 style={{ fontSize: '2.5rem', fontWeight: 800, marginBottom: '1rem' }}>ماژول‌های پلتفرم</h2>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '1.1rem' }}>
              برای باز کردن هر ماژول، ابتدا وارد حساب کاربری شوید
            </p>
          </motion.div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.75rem' }}>
            {modules.map((m, i) => (
              <motion.div key={m.title} initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: (i % 4) * 0.08 }}>
                <ModuleCard {...m} />
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </PublicLayout>
  );
};
