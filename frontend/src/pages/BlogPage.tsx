import React from 'react';
import { motion } from 'framer-motion';
import { Clock, Tag } from 'lucide-react';
import { PublicLayout } from '../components/layout/PublicLayout';

const posts = [
  { title: 'چگونه بادشکن ۶۰٪ فرسایش بادی را کاهش می‌دهد؟', cat: 'فرسایش', color: '#f59e0b', time: '۶ دقیقه', date: '۱۴۰۵/۰۶/۰۱' },
  { title: 'راهنمای کامل کشت چندلایه (Agroforestry)', cat: 'کشاورزی', color: '#22c55e', time: '۹ دقیقه', date: '۱۴۰۵/۰۵/۲۰' },
  { title: 'اعتبار کربن چیست و چگونه درآمدزایی کنیم؟', cat: 'کربن', color: '#10b981', time: '۷ دقیقه', date: '۱۴۰۵/۰۵/۱۰' },
  { title: 'NDVI از فضا: پایش سلامت گیاه با ماهواره', cat: 'ماهواره', color: '#0ea5e9', time: '۵ دقیقه', date: '۱۴۰۵/۰۴/۲۸' },
  { title: 'بودجه آب مزرعه: نفوذ، رواناب، آبخوان', cat: 'آب', color: '#3b82f6', time: '۸ دقیقه', date: '۱۴۰۵/۰۴/۱۵' },
  { title: 'اقتصاد گله: سودآوری واقعی دامداری', cat: 'دامداری', color: '#b45309', time: '۶ دقیقه', date: '۱۴۵/۰/۰۲' },
];

export const BlogPage: React.FC = () => (
  <PublicLayout>
    <section style={{ maxWidth: 1200, margin: '0 auto', padding: '7rem 2rem 5rem' }}>
      <h1 style={{ fontSize: '2.5rem', fontWeight: 800, textAlign: 'center', marginBottom: '3rem' }}>وبلاگ Eco Nojin</h1>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.75rem' }}>
        {posts.map((p, i) => (
          <motion.article key={i} initial={{ opacity: 0, y: 25 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: (i % 3) * 0.1 }}
            whileHover={{ y: -8 }} className="card" style={{ overflow: 'hidden', padding: 0, cursor: 'pointer' }}>
            <div style={{ height: 140, background: `linear-gradient(135deg, ${p.color}, ${p.color}88)`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span className="badge" style={{ background: 'rgba(255,255,255,0.25)', color: '#fff', backdropFilter: 'blur(6px)' }}><Tag size={12} /> {p.cat}</span>
            </div>
            <div style={{ padding: '1.5rem' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.9rem', lineHeight: 1.6 }}>{p.title}</h3>
              <div style={{ display: 'flex', gap: '1rem', color: 'var(--color-text-tertiary)', fontSize: '0.8rem' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><Clock size={12} /> {p.time}</span>
                <span>{p.date}</span>
              </div>
            </div>
          </motion.article>
        ))}
      </div>
    </section>
  </PublicLayout>
);
