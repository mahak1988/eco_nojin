'use client';
import { useState } from 'react';
import Footer from '../../components/layout/Footer';
import { useI18n } from '../../lib/i18n-context';

export default function ContactPage() {
  const { t, direction } = useI18n();
  const [formData, setFormData] = useState({ name: '', email: '', subject: '', message: '' });
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 3000);
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '12px 16px',
    borderRadius: '8px',
    border: '1px solid #d1d5db',
    fontSize: '1rem',
    marginBottom: '16px',
  };

  return (
    <div dir={direction}>
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '60px 32px' }}>
        <h1 style={{ fontSize: '3rem', fontWeight: 'bold', color: '#065f46', marginBottom: '16px' }}>
          {t('contact_title')}
        </h1>
        <p style={{ fontSize: '1.1rem', color: '#6b7280', marginBottom: '48px' }}>
          {t('contact_subtitle')}
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '48px' }}>
          <div>
            <h2 style={{ color: '#065f46', marginBottom: '24px' }}>{t('contact_form_title')}</h2>
            <form onSubmit={handleSubmit}>
              <input
                type="text"
                placeholder={t('contact_name')}
                aria-label={t('contact_name')}
                style={inputStyle}
                value={formData.name}
                onChange={e => setFormData({ ...formData, name: e.target.value })}
                required
              />
              <input
                type="email"
                placeholder={t('contact_email')}
                aria-label={t('contact_email')}
                style={inputStyle}
                value={formData.email}
                onChange={e => setFormData({ ...formData, email: e.target.value })}
                required
              />
              <input
                type="text"
                placeholder={t('contact_subject')}
                aria-label={t('contact_subject')}
                style={inputStyle}
                value={formData.subject}
                onChange={e => setFormData({ ...formData, subject: e.target.value })}
                required
              />
              <textarea
                placeholder={t('contact_message')}
                rows={6}
                style={{ ...inputStyle, resize: 'vertical' }}
                value={formData.message}
                onChange={e => setFormData({ ...formData, message: e.target.value })}
                required
              />
              <button
                type="submit"
                style={{
                  padding: '14px 32px',
                  background: '#10b981',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
              >
                {submitted ? '✓ ' + t('contact_sent') : t('contact_send')}
              </button>
            </form>
          </div>

          <div>
            <h2 style={{ color: '#065f46', marginBottom: '24px' }}>{t('contact_info_title')}</h2>
            <div style={{
              background: '#f0fdf4',
              padding: '32px',
              borderRadius: '12px',
              marginBottom: '24px',
            }}>
              {[
                { icon: '📧', label: t('contact_email_label'), value: 'info@econojin.org' },
                { icon: '📞', label: t('contact_phone_label'), value: '+98 21 1234 5678' },
                { icon: '📍', label: t('contact_address_label'), value: t('contact_address_value') },
                { icon: '🕒', label: t('contact_hours_label'), value: t('contact_hours_value') },
              ].map(item => (
                <div key={item.label} style={{
                  display: 'flex', alignItems: 'center', gap: '16px',
                  marginBottom: '20px',
                }}>
                  <span style={{ fontSize: '1.5rem' }}>{item.icon}</span>
                  <div>
                    <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>{item.label}</div>
                    <div style={{ fontWeight: '500', color: '#065f46' }}>{item.value}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}
