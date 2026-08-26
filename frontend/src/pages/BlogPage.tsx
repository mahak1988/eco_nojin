import React from 'react';
import { motion } from 'framer-motion';
import { Calendar, Clock, User, ArrowLeft } from 'lucide-react';
import { PublicLayout } from '../components/layout/PublicLayout';
import { Card } from '../components/ui';

const BLOG_POSTS = [
  {
    id: '1',
    title: 'چگونه با بادشکن‌ها فرسایش بادی را ۶۰٪ کاهش دهیم؟',
    excerpt: 'راهنمای کامل طراحی و اجرای بادشکن‌های علمی بر اساس تحقیقات FAO و WEPS...',
    author: 'دکتر محمد رضایی',
    date: '۱۴۰۵/۰۶/۰۵',
    readTime: '۸ دقیقه',
    category: 'مهندسی آبخیزداری',
    image: '🌳',
  },
  {
    id: '2',
    title: 'ترسیب کربن در خاک: فرصتی برای درآمدزایی پایدار',
    excerpt: 'بررسی مدل RothC و نحوه تبدیل کربن ذخیره‌شده در خاک به اعتبار کربن...',
    author: 'مهندس سارا احمدی',
    date: '۱۴۰۵/۰۶/۰۱',
    readTime: '۱۲ دقیقه',
    category: 'اقتصاد پایدار',
    image: '🌱',
  },
  {
    id: '3',
    title: 'کشت چندلایه: آینده کشاورزی در ایران',
    excerpt: 'چگونه سیستم‌های Agroforestry می‌توانند عملکرد را ۲۵٪ افزایش دهند...',
    author: 'دکتر علی کریمی',
    date: '۱۴۰۵/۰۵/۲۸',
    readTime: '۱۰ دقیقه',
    category: 'کشاورزی پایدار',
    image: '🌾',
  },
  {
    id: '4',
    title: 'مدیریت هوشمند آب با HyDroMa',
    excerpt: 'معرفی الگوریتم‌های پیشرفته کاهش مصرف آب تا ۴۰٪ در کشاورزی...',
    author: 'مهندس نیما حسینی',
    date: '۱۴۰۵/۰۵/۲۰',
    readTime: '۱۵ دقیقه',
    category: 'مدیریت آب',
    image: '💧',
  },
  {
    id: '5',
    title: 'از خاک تا بلاکچین: سفر کربن',
    excerpt: 'چگونه کشاورزان می‌توانند از طریق توکنایز کردن کربن، درآمد کسب کنند...',
    author: 'دکتر مریم صادقی',
    date: '۱۴۰۵/۰۵/۱۵',
    readTime: '۹ دقیقه',
    category: 'بلاکچین',
    image: '🔗',
  },
  {
    id: '6',
    title: 'مدل AquaCrop: راهنمای کامل',
    excerpt: 'شبیه‌سازی رشد گیاه و نیاز آبی با استفاده از مدل FAO AquaCrop...',
    author: 'دکتر حسن محمدی',
    date: '۱۴۰۵/۰۵/۱۰',
    readTime: '۲۰ دقیقه',
    category: 'مدل‌سازی',
    image: '📊',
  },
];

export const BlogPage: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = React.useState<string>('همه');

  const categories = ['همه', 'مهندسی آبخیزداری', 'اقتصاد پایدار', 'کشاورزی پایدار', 'مدیریت آب', 'بلاکچین', 'مدل‌سازی'];

  const filteredPosts = selectedCategory === 'همه'
    ? BLOG_POSTS
    : BLOG_POSTS.filter(p => p.category === selectedCategory);

  return (
    <PublicLayout>
      <section style={{ padding: '6rem 2rem', maxWidth: 1400, margin: '0 auto' }}>
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ textAlign: 'center', marginBottom: '3rem' }}
        >
          <h1 style={{ fontSize: '3rem', fontWeight: 700, marginBottom: '1rem' }}>
            وبلاگ <span className="logo-eco-nojin">Eco Nojin</span>
          </h1>
          <p style={{ fontSize: '1.25rem', color: 'var(--color-text-secondary)', maxWidth: 700, margin: '0 auto' }}>
            آخرین مقالات و تحقیقات در حوزه کشاورزی پایدار، مدیریت منابع آب و فناوری‌های نوین
          </p>
        </motion.div>

        {/* Category Filter */}
        <div style={{
          display: 'flex',
          gap: '0.5rem',
          marginBottom: '3rem',
          justifyContent: 'center',
          flexWrap: 'wrap',
        }}>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`btn ${selectedCategory === cat ? 'btn-primary' : 'btn-secondary'}`}
              style={{ fontSize: '0.875rem' }}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Posts Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
          gap: '2rem',
        }}>
          {filteredPosts.map((post, index) => (
            <motion.article
              key={post.id}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ y: -8 }}
              className="card"
              style={{ padding: 0, overflow: 'hidden', cursor: 'pointer' }}
            >
              {/* Image Header */}
              <div style={{
                height: 200,
                background: 'linear-gradient(135deg, var(--color-primary), var(--color-info))',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '5rem',
              }}>
                {post.image}
              </div>

              {/* Content */}
              <div style={{ padding: '1.5rem' }}>
                <div style={{
                  display: 'inline-block',
                  padding: '0.25rem 0.75rem',
                  background: 'var(--color-primary)',
                  color: 'white',
                  borderRadius: 'var(--radius-full)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  marginBottom: '1rem',
                }}>
                  {post.category}
                </div>

                <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.75rem', lineHeight: 1.4 }}>
                  {post.title}
                </h3>

                <p style={{
                  color: 'var(--color-text-secondary)',
                  lineHeight: 1.7,
                  marginBottom: '1rem',
                  fontSize: '0.875rem',
                }}>
                  {post.excerpt}
                </p>

                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem',
                  fontSize: '0.75rem',
                  color: 'var(--color-text-tertiary)',
                  borderTop: '1px solid var(--color-border)',
                  paddingTop: '1rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <User size={14} />
                    <span>{post.author}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <Calendar size={14} />
                    <span>{post.date}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', marginRight: 'auto' }}>
                    <Clock size={14} />
                    <span>{post.readTime}</span>
                  </div>
                </div>

                <div style={{
                  marginTop: '1rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  color: 'var(--color-primary)',
                  fontWeight: 600,
                  fontSize: '0.875rem',
                }}>
                  ادامه مطلب
                  <ArrowLeft size={16} />
                </div>
              </div>
            </motion.article>
          ))}
        </div>
      </section>
    </PublicLayout>
  );
};
