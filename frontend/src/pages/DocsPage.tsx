import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Book, Search, FileText, Code, Terminal, Layers } from 'lucide-react';
import { PublicLayout } from '../components/layout/PublicLayout';
import { Card, Button } from '../components/ui';

const DOCS_SECTIONS = [
  {
    id: 'getting-started',
    title: 'شروع سریع',
    icon: <Terminal size={24} />,
    description: 'راهنمای نصب و راه‌اندازی اولیه',
    articles: [
      { title: 'نصب و راه‌اندازی', time: '5 دقیقه' },
      { title: 'ایجاد اولین پروژه', time: '10 دقیقه' },
      { title: 'آشنایی با رابط کاربری', time: '8 دقیقه' },
    ],
  },
  {
    id: 'simulation',
    title: 'شبیه‌سازها',
    icon: <Layers size={24} />,
    description: 'استفاده از شبیه‌سازهای علمی',
    articles: [
      { title: 'AquaCrop - رشد گیاه', time: '15 دقیقه' },
      { title: 'RothC - کربن خاک', time: '12 دقیقه' },
      { title: 'SWAT+ - هیدرولوژی', time: '20 دقیقه' },
      { title: 'WEPS - فرسایش بادی', time: '10 دقیقه' },
      { title: 'RUSLE - فرسایش آبی', time: '10 دقیقه' },
    ],
  },
  {
    id: 'api',
    title: 'API Reference',
    icon: <Code size={24} />,
    description: 'مستندات کامل API',
    articles: [
      { title: 'Authentication', time: '5 دقیقه' },
      { title: 'Simulation Endpoints', time: '20 دقیقه' },
      { title: 'Livestock API', time: '15 دقیقه' },
      { title: 'Blockchain Integration', time: '25 دقیقه' },
    ],
  },
  {
    id: 'guides',
    title: 'راهنماهای کاربردی',
    icon: <Book size={24} />,
    description: 'مقالات آموزشی عمیق',
    articles: [
      { title: 'طراحی بادشکن بهینه', time: '30 دقیقه' },
      { title: 'مدیریت منابع آب', time: '25 دقیقه' },
      { title: 'کشت چندلایه', time: '20 دقیقه' },
      { title: 'کسب درآمد از کربن', time: '35 دقیقه' },
    ],
  },
];

export const DocsPage: React.FC = () => {
  const [selectedSection, setSelectedSection] = useState('getting-started');
  const [searchQuery, setSearchQuery] = useState('');

  const activeSection = DOCS_SECTIONS.find(s => s.id === selectedSection);

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
            مستندات <span className="logo-eco-nojin">Eco Nojin</span>
          </h1>
          <p style={{ fontSize: '1.25rem', color: 'var(--color-text-secondary)' }}>
            همه چیز برای شروع، استفاده و توسعه روی پلتفرم Eco Nojin
          </p>
        </motion.div>

        {/* Search */}
        <div style={{ maxWidth: 600, margin: '0 auto 3rem', position: 'relative' }}>
          <Search
            size={20}
            style={{
              position: 'absolute',
              right: '1rem',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--color-text-tertiary)',
            }}
          />
          <input
            type="text"
            placeholder="جستجو در مستندات..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input"
            style={{ paddingLeft: '1rem', paddingRight: '3rem', height: 56, fontSize: '1rem' }}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '2rem' }}>
          {/* Sidebar */}
          <div>
            <div style={{
              position: 'sticky',
              top: 100,
              background: 'var(--color-surface)',
              borderRadius: 'var(--radius-xl)',
              padding: '1rem',
              border: '1px solid var(--color-border)',
            }}>
              <h3 style={{ fontSize: '0.875rem', fontWeight: 700, marginBottom: '1rem', padding: '0 0.5rem' }}>
                بخش‌ها
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                {DOCS_SECTIONS.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => setSelectedSection(section.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.75rem',
                      padding: '0.75rem',
                      borderRadius: 'var(--radius-lg)',
                      border: 'none',
                      background: selectedSection === section.id ? 'var(--color-primary)' : 'transparent',
                      color: selectedSection === section.id ? 'white' : 'var(--color-text-secondary)',
                      cursor: 'pointer',
                      textAlign: 'right',
                      fontSize: '0.875rem',
                      transition: 'all 0.2s',
                    }}
                  >
                    {section.icon}
                    <span>{section.title}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Content */}
          <motion.div
            key={selectedSection}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            {activeSection && (
              <>
                <Card
                  title={activeSection.title}
                  icon={activeSection.icon}
                  subtitle={activeSection.description}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {activeSection.articles.map((article, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        whileHover={{ x: 4 }}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '1rem',
                          background: 'var(--color-surface)',
                          borderRadius: 'var(--radius-lg)',
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <FileText size={18} color="var(--color-primary)" />
                          <span style={{ fontWeight: 500 }}>{article.title}</span>
                        </div>
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>
                          {article.time}
                        </span>
                      </motion.div>
                    ))}
                  </div>
                </Card>

                {/* Quick Start CTA */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  style={{
                    marginTop: '2rem',
                    padding: '2rem',
                    background: 'linear-gradient(135deg, var(--color-primary), var(--color-info))',
                    borderRadius: 'var(--radius-2xl)',
                    color: 'white',
                    textAlign: 'center',
                  }}
                >
                  <h3 style={{ marginBottom: '0.75rem' }}>نیاز به کمک دارید؟</h3>
                  <p style={{ marginBottom: '1.5rem', opacity: 0.9 }}>
                    تیم پشتیبانی ما ۲۴ ساعته آماده کمک به شماست
                  </p>
                  <Button variant="secondary" style={{ background: 'white', color: 'var(--color-primary)' }}>
                    تماس با پشتیبانی
                  </Button>
                </motion.div>
              </>
            )}
          </motion.div>
        </div>
      </section>
    </PublicLayout>
  );
};
