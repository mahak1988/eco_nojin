import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, Phone, MapPin, Send, MessageCircle, Clock, CheckCircle } from 'lucide-react';
import { PublicLayout } from '../components/layout/PublicLayout';
import { Card, Button, GlassMorphismCard } from '../components/ui';

export const ContactPage: React.FC = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: '',
  });
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
    setTimeout(() => {
      setSubmitted(false);
      setFormData({ name: '', email: '', subject: '', message: '' });
    }, 3000);
  };

  const contactMethods = [
    {
      icon: <Mail size={24} />,
      title: 'ایمیل',
      value: 'info@econojin.com',
      description: 'پاسخ در کمتر از ۲۴ ساعت',
      color: '#3b82f6',
    },
    {
      icon: <Phone size={24} />,
      title: 'تلفن',
      value: '+98 21 1234 5678',
      description: 'شنبه تا چهارشنبه ۹-۱۷',
      color: '#10b981',
    },
    {
      icon: <MessageCircle size={24} />,
      title: 'چت زنده',
      value: 'پشتیبانی آنلاین',
      description: 'پاسخ فوری در ساعات کاری',
      color: '#f59e0b',
    },
    {
      icon: <MapPin size={24} />,
      title: 'دفتر مرکزی',
      value: 'تهران، خیابان ولیعصر',
      description: 'مراجعه حضوری با هماهنگی',
      color: '#8b5cf6',
    },
  ];

  return (
    <PublicLayout>
      <section style={{ padding: '6rem 2rem', maxWidth: 1400, margin: '0 auto' }}>
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ textAlign: 'center', marginBottom: '4rem' }}
        >
          <h1 style={{ fontSize: '3rem', fontWeight: 700, marginBottom: '1rem' }}>تماس با ما</h1>
          <p
            style={{
              fontSize: '1.25rem',
              color: 'var(--color-text-secondary)',
              maxWidth: 600,
              margin: '0 auto',
            }}
          >
            سوالی دارید؟ ما اینجاییم تا کمک کنیم. از هر طریقی که راحت‌ترید با ما در ارتباط باشید.
          </p>
        </motion.div>

        {/* Contact Methods */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '1.5rem',
            marginBottom: '4rem',
          }}
        >
          {contactMethods.map((method, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ y: -8 }}
            >
              <GlassMorphismCard
                icon={method.icon}
                title={method.title}
                gradient={`linear-gradient(135deg, ${method.color}, ${method.color}80)`}
              >
                <div style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                  {method.value}
                </div>
                <p
                  style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem', margin: 0 }}
                >
                  {method.description}
                </p>
              </GlassMorphismCard>
            </motion.div>
          ))}
        </div>

        {/* Contact Form */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3rem' }}>
          <Card title="فرم تماس" icon={<Send size={20} />}>
            {submitted ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                style={{
                  textAlign: 'center',
                  padding: '3rem 2rem',
                }}
              >
                <CheckCircle
                  size={64}
                  color="var(--color-success)"
                  style={{ marginBottom: '1rem' }}
                />
                <h3 style={{ marginBottom: '0.5rem' }}>پیام شما با موفقیت ارسال شد!</h3>
                <p style={{ color: 'var(--color-text-secondary)' }}>
                  در اسرع وقت با شما تماس خواهیم گرفت.
                </p>
              </motion.div>
            ) : (
              <form onSubmit={handleSubmit}>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '1rem',
                    marginBottom: '1rem',
                  }}
                >
                  <div>
                    <label
                      style={{
                        display: 'block',
                        marginBottom: '0.5rem',
                        fontSize: '0.875rem',
                        fontWeight: 500,
                      }}
                    >
                      نام و نام خانوادگی
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="input"
                      placeholder="نام شما"
                    />
                  </div>
                  <div>
                    <label
                      style={{
                        display: 'block',
                        marginBottom: '0.5rem',
                        fontSize: '0.875rem',
                        fontWeight: 500,
                      }}
                    >
                      ایمیل
                    </label>
                    <input
                      type="email"
                      required
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="input"
                      placeholder="email@example.com"
                      dir="ltr"
                    />
                  </div>
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <label
                    style={{
                      display: 'block',
                      marginBottom: '0.5rem',
                      fontSize: '0.875rem',
                      fontWeight: 500,
                    }}
                  >
                    موضوع
                  </label>
                  <select
                    required
                    value={formData.subject}
                    onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                    className="input"
                  >
                    <option value="">انتخاب کنید...</option>
                    <option value="general">سوال عمومی</option>
                    <option value="technical">پشتیبانی فنی</option>
                    <option value="sales">فروش و قیمت‌گذاری</option>
                    <option value="partnership">همکاری</option>
                    <option value="feedback">بازخورد</option>
                  </select>
                </div>

                <div style={{ marginBottom: '1.5rem' }}>
                  <label
                    style={{
                      display: 'block',
                      marginBottom: '0.5rem',
                      fontSize: '0.875rem',
                      fontWeight: 500,
                    }}
                  >
                    پیام شما
                  </label>
                  <textarea
                    required
                    rows={6}
                    value={formData.message}
                    onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                    className="input"
                    placeholder="پیام خود را اینجا بنویسید..."
                    style={{ resize: 'vertical', minHeight: 120 }}
                  />
                </div>

                <Button variant="primary" type="submit" style={{ width: '100%' }}>
                  <Send size={16} />
                  ارسال پیام
                </Button>
              </form>
            )}
          </Card>

          {/* FAQ */}
          <Card title="سوالات متداول" icon={<MessageCircle size={20} />}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {[
                {
                  q: 'چقدر طول می‌کشد تا پاسخ بگیرید؟',
                  a: 'معمولاً در کمتر از ۲۴ ساعت کاری پاسخ می‌دهیم. برای موارد فوری از چت زنده استفاده کنید.',
                },
                {
                  q: 'آیا مشاوره رایگان ارائه می‌دهید؟',
                  a: 'بله، برای کشاورزان و کارشناسان آبخیزداری مشاوره اولیه رایگان ارائه می‌شود.',
                },
                {
                  q: 'چگونه می‌توانم دموی پلتفرم را ببینم؟',
                  a: 'از طریق فرم تماس یا ایمیل درخواست دهید، هماهنگی برای ارائه آنلاین انجام می‌شود.',
                },
                {
                  q: 'آیا امکان سفارشی‌سازی پلتفرم وجود دارد؟',
                  a: 'بله، پلن Enterprise امکانات سفارشی‌سازی کامل را فراهم می‌کند.',
                },
              ].map((faq, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  style={{
                    padding: '1rem',
                    background: 'var(--color-surface)',
                    borderRadius: 'var(--radius-lg)',
                    borderRight: '4px solid var(--color-primary)',
                  }}
                >
                  <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem' }}>{faq.q}</h4>
                  <p
                    style={{
                      margin: 0,
                      color: 'var(--color-text-secondary)',
                      fontSize: '0.875rem',
                      lineHeight: 1.7,
                    }}
                  >
                    {faq.a}
                  </p>
                </motion.div>
              ))}
            </div>
          </Card>
        </div>

        {/* Office Hours */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            marginTop: '3rem',
            padding: '2rem',
            background: 'var(--color-surface)',
            borderRadius: 'var(--radius-xl)',
            textAlign: 'center',
          }}
        >
          <Clock size={32} color="var(--color-primary)" style={{ marginBottom: '1rem' }} />
          <h3 style={{ marginBottom: '1rem' }}>ساعات کاری</h3>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '2rem',
              maxWidth: 600,
              margin: '0 auto',
            }}
          >
            <div>
              <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>شنبه تا چهارشنبه</div>
              <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
                ۹:۰۰ - ۱۷:۰۰
              </div>
            </div>
            <div>
              <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>پنج‌شنبه</div>
              <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
                ۹:۰۰ - ۱۳:۰۰
              </div>
            </div>
            <div>
              <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>جمعه</div>
              <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
                تعطیل
              </div>
            </div>
          </div>
        </motion.div>
      </section>
    </PublicLayout>
  );
};
