import React from 'react';
import { motion } from 'framer-motion';
import { PublicLayout } from '../components/layout/PublicLayout';
import { Droplets, Leaf, Globe, Heart } from 'lucide-react';

const goals = [
  {
    icon: Droplets,
    title: 'بحران آب',
    description: 'کاهش ۴۰٪ مصرف آب در کشاورزی با الگوریتم‌های هوشمند آبیاری',
    stat: '۷۰٪',
    statLabel: 'مصرف آب کشاورزی',
  },
  {
    icon: Leaf,
    title: 'فرسایش خاک',
    description: 'حفاظت از ۱ میلیون هکتار زمین کشاورزی در برابر فرسایش',
    stat: '۲۵ میلیارد',
    statLabel: 'تن خاک از دست رفته سالانه',
  },
  {
    icon: Globe,
    title: 'تغییرات اقلیمی',
    description: 'کاهش ۳۰٪ انتشار گازهای گلخانه‌ای از بخش کشاورزی',
    stat: '۲۴٪',
    statLabel: 'از انتشار جهانی',
  },
  {
    icon: Heart,
    title: 'امنیت غذایی',
    description: 'افزایش ۵۰٪ عملکرد محصول با حفظ پایداری',
    stat: '۸۰۰ میلیون',
    statLabel: 'نفر گرسنه در جهان',
  },
];

export const MissionPage: React.FC = () => {
  return (
    <PublicLayout>
      {/* Hero */}
      <section
        style={{
          minHeight: '60vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '6rem 2rem',
          background:
            'linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%)',
          textAlign: 'center',
        }}
      >
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          style={{ maxWidth: 900 }}
        >
          <h1
            style={{
              fontSize: 'clamp(2.5rem, 6vw, 4rem)',
              fontWeight: 700,
              marginBottom: '1.5rem',
            }}
          >
            مأموریت ما
          </h1>
          <p
            style={{
              fontSize: '1.5rem',
              lineHeight: 1.8,
              color: 'var(--color-text-secondary)',
              marginBottom: '2rem',
            }}
          >
            <span className="gradient-text" style={{ fontWeight: 600 }}>
              "نجات زمین، قطره به قطره، دانه به دانه"
            </span>
          </p>
          <p
            style={{ fontSize: '1.125rem', lineHeight: 1.8, color: 'var(--color-text-secondary)' }}
          >
            ما معتقدیم که کشاورزی می‌تواند همزمان مولد و پایدار باشد.
            <br />
            با ابزارهای هوشمند، می‌توانیم به کشاورزان کمک کنیم تا با منابع کمتر، محصول بیشتری تولید
            کنند و در عین حال از سیاره زمین محافظت کنند.
          </p>
        </motion.div>
      </section>

      {/* Goals */}
      <section style={{ padding: '6rem 2rem' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <h2
            style={{
              fontSize: '2.5rem',
              fontWeight: 700,
              textAlign: 'center',
              marginBottom: '4rem',
            }}
          >
            چالش‌هایی که حل می‌کنیم
          </h2>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '2rem',
            }}
          >
            {goals.map((goal, index) => {
              const Icon = goal.icon;
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  viewport={{ once: true }}
                  className="card"
                  style={{ padding: '2rem' }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '1rem',
                      marginBottom: '1.5rem',
                    }}
                  >
                    <div
                      style={{
                        width: 56,
                        height: 56,
                        borderRadius: 'var(--radius-xl)',
                        background: 'var(--color-primary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                      }}
                    >
                      <Icon size={28} />
                    </div>
                    <div>
                      <div
                        style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--color-primary)' }}
                      >
                        {goal.stat}
                      </div>
                      <div style={{ fontSize: '0.875rem', color: 'var(--color-text-tertiary)' }}>
                        {goal.statLabel}
                      </div>
                    </div>
                  </div>
                  <h3 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '0.75rem' }}>
                    {goal.title}
                  </h3>
                  <p style={{ color: 'var(--color-text-secondary)', lineHeight: 1.7, margin: 0 }}>
                    {goal.description}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Slogans */}
      <section style={{ padding: '6rem 2rem', background: 'var(--color-surface)' }}>
        <div style={{ maxWidth: 1000, margin: '0 auto', textAlign: 'center' }}>
          <h2 style={{ fontSize: '2.5rem', fontWeight: 700, marginBottom: '3rem' }}>شعارهای ما</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {[
              {
                en: 'From Drop to Ocean, From Seed to Forest',
                fa: 'از قطره تا اقیانوس، از دانه تا جنگل',
              },
              { en: 'Smart Farming, Sustainable Future', fa: 'کشاورزی هوشمند، آینده پایدار' },
              { en: 'Every Field Tells a Story', fa: 'هر زمین داستانی دارد' },
              { en: 'Technology Meets Tradition', fa: 'فناوری در خدمت سنت' },
            ].map((slogan, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: index % 2 === 0 ? -30 : 30 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                className="card"
                style={{ padding: '2rem' }}
              >
                <p
                  className="font-english"
                  style={{
                    fontSize: '1.5rem',
                    fontWeight: 600,
                    color: 'var(--color-primary)',
                    marginBottom: '0.5rem',
                  }}
                >
                  "{slogan.en}"
                </p>
                <p
                  className="font-persian"
                  style={{
                    fontSize: '1.25rem',
                    color: 'var(--color-text-secondary)',
                    margin: 0,
                  }}
                >
                  {slogan.fa}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </PublicLayout>
  );
};
