import React from 'react';
import { Logo } from '../ui/Logo';
import { Mail, Phone, MapPin } from 'lucide-react';

export const PublicFooter: React.FC = () => {
  return (
    <footer
      style={{
        background: 'var(--color-surface)',
        borderTop: '1px solid var(--color-border)',
        padding: '4rem 2rem 2rem',
      }}
    >
      <div style={{ maxWidth: 1400, margin: '0 auto' }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '3rem',
            marginBottom: '3rem',
          }}
        >
          {/* Brand */}
          <div>
            <Logo size="md" />
            <p
              style={{
                marginTop: '1rem',
                color: 'var(--color-text-secondary)',
                lineHeight: 1.8,
                fontSize: '0.875rem',
              }}
            >
              پلتفرم یکپارچه برای کشاورزی پایدار، مدیریت منابع آب، و مقابله با تغییرات اقلیمی
            </p>
          </div>

          {/* Links */}
          <div>
            <h4 style={{ marginBottom: '1rem', color: 'var(--color-text-primary)' }}>
              دسترسی سریع
            </h4>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {['خانه', 'درباره ما', 'ویژگی‌ها', 'قیمت‌گذاری', 'وبلاگ'].map((item) => (
                <li key={item} style={{ marginBottom: '0.5rem' }}>
                  <a
                    href="#"
                    style={{
                      color: 'var(--color-text-secondary)',
                      textDecoration: 'none',
                      fontSize: '0.875rem',
                      transition: 'color 0.2s',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--color-primary)')}
                    onMouseLeave={(e) =>
                      (e.currentTarget.style.color = 'var(--color-text-secondary)')
                    }
                  >
                    {item}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 style={{ marginBottom: '1rem', color: 'var(--color-text-primary)' }}>تماس با ما</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  color: 'var(--color-text-secondary)',
                  fontSize: '0.875rem',
                }}
              >
                <Mail size={16} />
                <span>info@econojin.com</span>
              </div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  color: 'var(--color-text-secondary)',
                  fontSize: '0.875rem',
                }}
              >
                <Phone size={16} />
                <span>+98 21 1234 5678</span>
              </div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  color: 'var(--color-text-secondary)',
                  fontSize: '0.875rem',
                }}
              >
                <MapPin size={16} />
                <span>تهران، ایران</span>
              </div>
            </div>
          </div>

          {/* Newsletter */}
          <div>
            <h4 style={{ marginBottom: '1rem', color: 'var(--color-text-primary)' }}>خبرنامه</h4>
            <p
              style={{
                color: 'var(--color-text-secondary)',
                fontSize: '0.875rem',
                marginBottom: '1rem',
              }}
            >
              برای دریافت آخرین اخبار و به‌روزرسانی‌ها عضو شوید
            </p>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                type="email"
                placeholder="ایمیل شما"
                className="input"
                style={{ flex: 1, fontSize: '0.875rem' }}
              />
              <button className="btn btn-primary" style={{ padding: '0.75rem 1rem' }}>
                عضویت
              </button>
            </div>
          </div>
        </div>

        {/* Bottom */}
        <div
          style={{
            borderTop: '1px solid var(--color-border)',
            paddingTop: '2rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '1rem',
          }}
        >
          <p style={{ color: 'var(--color-text-tertiary)', fontSize: '0.875rem', margin: 0 }}>
            © 2026 Eco Nojin × HyDroMa. تمامی حقوق محفوظ است.
          </p>
          <div style={{ display: 'flex', gap: '1.5rem' }}>
            <a
              href="#"
              style={{
                color: 'var(--color-text-tertiary)',
                fontSize: '0.875rem',
                textDecoration: 'none',
              }}
            >
              حریم خصوصی
            </a>
            <a
              href="#"
              style={{
                color: 'var(--color-text-tertiary)',
                fontSize: '0.875rem',
                textDecoration: 'none',
              }}
            >
              قوانین
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};
