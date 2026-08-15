'use client';
import { useState } from 'react';
import Sidebar from '../../components/layout/Sidebar';
import TopBar from '../../components/layout/TopBar';
import { useI18n } from '../../lib/i18n-context';

export default function SettingsPage() {
  const { t, locale, setLocale } = useI18n();
  const [theme, setTheme] = useState('light');
  const [notifications, setNotifications] = useState({ email: true, sms: true, push: false });

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f9fafb' }}>
      <Sidebar />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <TopBar />
        <main style={{ flex: 1, padding: '32px', maxWidth: '900px' }}>
          <h1 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '32px', color: '#111827' }}>
            {t('settings_title')}
          </h1>

          {/* Language */}
          <section style={{
            background: 'white', padding: '24px', borderRadius: '12px',
            marginBottom: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
          }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '16px' }}>
              🌐 {t('settings_language')}
            </h2>
            <select
              value={locale}
              onChange={(e) => setLocale(e.target.value)}
              style={{
                padding: '10px 16px', borderRadius: '6px',
                border: '1px solid #d1d5db', fontSize: '1rem',
              }}
            >
              <option value="en">English</option>
              <option value="fa">فارسی</option>
              <option value="ar">العربية</option>
              <option value="fr">Français</option>
              <option value="es">Español</option>
            </select>
          </section>

          {/* Appearance */}
          <section style={{
            background: 'white', padding: '24px', borderRadius: '12px',
            marginBottom: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
          }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '16px' }}>
              🎨 {t('settings_appearance')}
            </h2>
            <div style={{ display: 'flex', gap: '12px' }}>
              {['light', 'dark', 'auto'].map(opt => (
                <button
                  key={opt}
                  onClick={() => setTheme(opt)}
                  style={{
                    padding: '10px 20px', borderRadius: '6px',
                    border: theme === opt ? '2px solid #10b981' : '1px solid #d1d5db',
                    background: theme === opt ? '#d1fae5' : 'white',
                    cursor: 'pointer', fontWeight: theme === opt ? '600' : '400',
                  }}
                >
                  {t(`settings_theme_${opt}`)}
                </button>
              ))}
            </div>
          </section>

          {/* Notifications */}
          <section style={{
            background: 'white', padding: '24px', borderRadius: '12px',
            marginBottom: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
          }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '16px' }}>
              🔔 {t('settings_notifications')}
            </h2>
            {Object.entries(notifications).map(([key, val]) => (
              <label key={key} style={{
                display: 'flex', justifyContent: 'space-between',
                alignItems: 'center', padding: '12px 0',
                borderBottom: '1px solid #f3f4f6',
              }}>
                <span>{t(`settings_notif_${key}`)}</span>
                <input
                  type="checkbox"
                  checked={val}
                  onChange={(e) => setNotifications({ ...notifications, [key]: e.target.checked })}
                  style={{ width: '20px', height: '20px', cursor: 'pointer' }}
                />
              </label>
            ))}
          </section>

          {/* Privacy */}
          <section style={{
            background: 'white', padding: '24px', borderRadius: '12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
          }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '16px' }}>
              🔒 {t('settings_privacy')}
            </h2>
            <p style={{ color: '#6b7280', marginBottom: '16px' }}>{t('settings_privacy_desc')}</p>
            <button style={{
              padding: '10px 20px', background: '#065f46',
              color: 'white', border: 'none', borderRadius: '6px',
              cursor: 'pointer', fontWeight: '500',
            }}>
              {t('settings_change_password')}
            </button>
          </section>
        </main>
      </div>
    </div>
  );
}
