'use client';
import Footer from '../../components/layout/Footer';
import { useI18n } from '../../lib/i18n-context';

export default function AboutPage() {
  const { t, direction } = useI18n();

  return (
    <div dir={direction}>
      <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '60px 32px' }}>
        <h1 style={{ fontSize: '3rem', fontWeight: 'bold', color: '#065f46', marginBottom: '24px' }}>
          {t('about_title')}
        </h1>
        <p style={{ fontSize: '1.2rem', color: '#374151', lineHeight: 1.8, marginBottom: '32px' }}>
          {t('about_intro')}
        </p>

        <div style={{
          background: '#f0fdf4',
          padding: '32px',
          borderRadius: '12px',
          borderInlineStart: '4px solid #10b981',
          marginBottom: '40px',
        }}>
          <h2 style={{ color: '#065f46', marginBottom: '16px' }}>{t('about_mission_title')}</h2>
          <p style={{ color: '#374151', lineHeight: 1.7 }}>{t('about_mission_text')}</p>
        </div>

        <h2 style={{ fontSize: '2rem', color: '#065f46', marginBottom: '24px' }}>
          {t('about_values_title')}
        </h2>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '24px',
          marginBottom: '40px',
        }}>
          {[
            { icon: '🌍', key: 'inclusion' },
            { icon: '🔬', key: 'science' },
            { icon: '🤝', key: 'transparency' },
            { icon: '🌱', key: 'sustainability' },
          ].map(v => (
            <div key={v.key} style={{
              background: 'white',
              padding: '24px',
              borderRadius: '12px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
              border: '1px solid #e5e7eb',
            }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>{v.icon}</div>
              <h3 style={{ color: '#065f46', marginBottom: '8px' }}>{t(`about_value_${v.key}_title`)}</h3>
              <p style={{ color: '#6b7280', fontSize: '0.9rem', lineHeight: 1.6 }}>{t(`about_value_${v.key}_desc`)}</p>
            </div>
          ))}
        </div>

        <h2 style={{ fontSize: '2rem', color: '#065f46', marginBottom: '24px' }}>
          {t('about_team_title')}
        </h2>
        <p style={{ color: '#374151', lineHeight: 1.8 }}>
          {t('about_team_text')}
        </p>
      </div>
      <Footer />
    </div>
  );
}
