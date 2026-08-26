import React from 'react';
import { motion } from 'framer-motion';
import { PublicLayout } from '../components/layout/PublicLayout';
import { Logo } from '../components/ui/Logo';
import { Leaf, Droplets, Heart, Target } from 'lucide-react';

const values = [
  {
    icon: Leaf,
    title: 'پایداری',
    description: 'تعهد به حفظ منابع طبیعی برای نسل‌های آینده' },
  {
    icon: Droplets,
    title: 'نوآوری',
    description: 'استفاده از آخرین فناوری‌ها برای حل چالش‌های کشاورزی' },
  {
    icon: Heart,
    title: 'جامعه',
    description: 'حمایت از کشاورزان و جوامع روستایی' },
  {
    icon: Target,
    title: 'دقت علمی',
    description: 'مبتنی بر تحقیقات علمی و استانداردهای بین‌المللی' },
];

export const AboutPage: React.FC = () => {
  return (
    <PublicLayout>
      <section style={{ padding: '6rem 2rem', maxWidth: 1200, margin: '0 auto' }}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          style={{ textAlign: 'center', marginBottom: '4rem' }}
        >
          <Logo size="md" />
          <h1 style={{ fontSize: '3rem', fontWeight: 700, marginTop: '2rem', marginBottom: '1.5rem' }}>
            درباره ما
          </h1>
          <p style={{ fontSize: '1.25rem', color: 'var(--color-text-secondary)', maxWidth: 800, margin: '0 auto', lineHeight: 1.8 }}>
            Eco Nojin و HyDroMa با هدف ایجاد تحول در کشاورزی ایران و جهان تأسیس شدند.
            ما معتقدیم که با ترکیب دانش سنتی و فناوری مدرن، می‌توانیم آینده‌ای پایدار بسازیم.
          </p>
        </motion.div>

        {/* Mission Statement */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="card"
          style={{ marginBottom: '4rem', padding: '3rem', textAlign: 'center' }}
        >
          <h2 style={{ fontSize: '2rem', fontWeight: 600, marginBottom: '1.5rem' }}>
            مأموریت ما
          </h2>
          <p style={{ fontSize: '1.125rem', lineHeight: 2, color: 'var(--color-text-secondary)' }}>
            <strong className="gradient-text">"از قطره تا اقیانوس، از دانه تا جنگل"</strong>
            <br /><br />
            ما اینجاییم تا به کشاورزان کمک کنیم با حفظ منابع طبیعی، عملکرد بیشتری داشته باشند.
            با استفاده از هوش مصنوعی، داده‌های ماهواره‌ای، و مدل‌های علمی، ابزارهایی می‌سازیم
            که تصمیم‌گیری را ساده‌تر و دقیق‌تر می‌کنند.
          </p>
        </motion.div>

        {/* Values */}
        <div style={{ marginBottom: '4rem' }}>
          <h2 style={{ fontSize: '2rem', fontWeight: 700, textAlign: 'center', marginBottom: '3rem' }}>
            ارزش‌های ما
          </h2>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '2rem' }}
          >
            {values.map((value, index) => {
              const Icon = value.icon;
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  viewport={{ once: true }}
                  className="card"
                  style={{ textAlign: 'center', padding: '2rem' }}
                >
                  <Icon size={48} style={{ color: 'var(--color-primary)', marginBottom: '1rem' }} />
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.75rem' }}>
                    {value.title}
                  </h3>
                  <p style={{ color: 'var(--color-text-secondary)', lineHeight: 1.7, margin: 0 }}>
                    {value.description}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Story */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          style={{ maxWidth: 800, margin: '0 auto' }}
        >
          <h2 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '1.5rem' }}>
            داستان ما
          </h2>
          <div style={{ fontSize: '1.125rem', lineHeight: 2, color: 'var(--color-text-secondary)' }}>
            <p style={{ marginBottom: '1.5rem' }}>
              همه چیز از یک سؤال ساده شروع شد: <strong>"چرا کشاورزان ایرانی با وجود داشتن زمین‌های حاصلخیز،
              با چالش‌های بزرگی مواجه هستند؟"</strong>
            </p>
            <p style={{ marginBottom: '1.5rem' }}>
              کمبود آب، فرسایش خاک، تغییرات اقلیمی، و عدم دسترسی به فناوری‌های مدرن، چالش‌هایی هستند
              که میلیون‌ها کشاورز با آنها دست و پنجه نرم می‌کنند.
            </p>
            <p style={{ marginBottom: '1.5rem' }}>
              <strong>HyDroMa</strong> (Hydrological Dynamic Model) با تمرکز بر مدیریت منابع آب شروع شد.
              سپس <strong>Eco Nojin</strong> (اکو نوژین - اکوسیستم نوین) متولد شد تا دیدگاه جامع‌تری
              به کشاورزی پایدار ارائه دهد.
            </p>
            <p>
              امروز، این دو پلتفرم با هم کار می‌کنند تا راه‌حل‌های یکپارچه‌ای برای تمام جنبه‌های
              کشاورزی مدرن ارائه دهند.
            </p>
          </div>
        </motion.div>
      </section>
    </PublicLayout>
  );
};
