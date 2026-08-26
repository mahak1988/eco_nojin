import React from 'react';
import { ShieldCheck, Lock, EyeOff, Database } from 'lucide-react';
import { PublicLayout } from '../components/layout/PublicLayout';

const items = [
  { icon: Lock, t: 'رمزنگاری سرتاسری', b: 'داده‌ها در انتقال (TLS) و در ذخیره‌سازی (AES-256) رمزنگاری می‌شوند.' },
  { icon: EyeOff, t: 'عدم فروش داده', b: 'داده شخصی شما هرگز به اشخاص ثالث فروخته نمی‌شود.' },
  { icon: Database, t: 'حداقل داده', b: 'فقط داده‌های لازم برای ارائه سرویس جمع‌آوری می‌شود.' },
  { icon: ShieldCheck, t: 'حق فراموشی', b: 'هر زمان بخواهید، داده‌های شما به‌طور کامل حذف می‌شود.' },
];

export const PrivacyPage: React.FC = () => (
  <PublicLayout>
    <section style={{ maxWidth: 960, margin: '0 auto', padding: '7rem 2rem 5rem' }}>
      <h1 style={{ fontSize: '2.5rem', fontWeight: 800, marginBottom: '1rem', textAlign: 'center' }}>حریم خصوصی</h1>
      <p style={{ textAlign: 'center', color: 'var(--color-text-secondary)', marginBottom: '3rem' }}>حریم شما، خط قرمز ماست.</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.5rem' }}>
        {items.map((it, i) => {
          const Icon = it.icon;
          return (
            <div key={i} className="card" style={{ padding: '1.75rem' }}>
              <Icon size={32} style={{ color: 'var(--color-primary)', marginBottom: '1rem' }} />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.6rem' }}>{it.t}</h3>
              <p style={{ color: 'var(--color-text-secondary)', lineHeight: 1.8, margin: 0 }}>{it.b}</p>
            </div>
          );
        })}
      </div>
    </section>
  </PublicLayout>
);
