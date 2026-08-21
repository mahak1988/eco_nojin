'use client';
import Link from 'next/link';
import Footer from '../../components/layout/Footer';
import { useI18n } from '../../lib/i18n-context';

export default function PricingPage() {
  const { t, direction } = useI18n();

  const plans = [
    {
      key: 'free',
      price: '0',
      color: '#6b7280',
      features: ['feature_soil', 'feature_basic_ai', 'feature_ussd', 'feature_language'],
      cta: 'pricing_cta_free',
      popular: false,
    },
    {
      key: 'pro',
      price: '10',
      color: '#10b981',
      features: ['feature_all_modules', 'feature_advanced_ai', 'feature_satellite', 'feature_carbon', 'feature_marketplace', 'feature_priority'],
      cta: 'pricing_cta_pro',
      popular: true,
    },
    {
      key: 'enterprise',
      price: '500',
      color: '#065f46',
      features: ['feature_everything', 'feature_api', 'feature_whitelabel', 'feature_custom', 'feature_dedicated', 'feature_sla'],
      cta: 'pricing_cta_enterprise',
      popular: false,
    },
  ];

  return (
    <div dir={direction}>
      <div style={{ padding: '80px 32px', background: '#f9fafb' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', textAlign: 'center' }}>
          <h1 style={{ fontSize: '3rem', fontWeight: 'bold', color: '#065f46', marginBottom: '16px' }}>
            {t('pricing_title')}
          </h1>
          <p style={{ fontSize: '1.2rem', color: '#6b7280', marginBottom: '60px' }}>
            {t('pricing_subtitle')}
          </p>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '32px',
            alignItems: 'stretch',
          }}>
            {plans.map(plan => (
              <div key={plan.key} style={{
                background: 'white',
                padding: '40px 32px',
                borderRadius: '16px',
                boxShadow: plan.popular ? '0 20px 40px rgba(16, 185, 129, 0.2)' : '0 4px 12px rgba(0,0,0,0.05)',
                border: plan.popular ? `2px solid ${plan.color}` : '1px solid #e5e7eb',
                position: 'relative',
                transform: plan.popular ? 'scale(1.05)' : 'scale(1)',
              }}>
                {plan.popular && (
                  <div style={{
                    position: 'absolute',
                    top: '-14px',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    background: plan.color,
                    color: 'white',
                    padding: '6px 20px',
                    borderRadius: '20px',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                  }}>
                    {t('pricing_popular')}
                  </div>
                )}
                <h3 style={{
                  fontSize: '1.5rem',
                  fontWeight: '600',
                  color: plan.color,
                  marginBottom: '8px',
                }}>{t(`pricing_plan_${plan.key}`)}</h3>
                <div style={{ marginBottom: '24px' }}>
                  <span style={{ fontSize: '3.5rem', fontWeight: 'bold', color: '#111827' }}>${plan.price}</span>
                  <span style={{ color: '#6b7280' }}>/ {t('pricing_per_month')}</span>
                </div>
                <ul style={{ listStyle: 'none', padding: 0, marginBottom: '32px', textAlign: 'start' }}>
                  {plan.features.map(f => (
                    <li key={f} style={{
                      padding: '10px 0',
                      borderBottom: '1px solid #f3f4f6',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                    }}>
                      <span style={{ color: '#10b981' }}>✓</span>
                      <span style={{ color: '#374151', fontSize: '0.95rem' }}>{t(`pricing_${f}`)}</span>
                    </li>
                  ))}
                </ul>
                <Link href="/register" style={{
                  display: 'block',
                  textAlign: 'center',
                  padding: '14px',
                  background: plan.color,
                  color: 'white',
                  borderRadius: '8px',
                  fontWeight: '600',
                }}>
                  {t(plan.cta)}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}
