"use client";
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Wallet, ArrowRight } from 'lucide-react';
import { useI18n } from '@/lib/i18n-context';
import { useTheme } from '@/lib/theme-context';
import { api } from '@/lib/api-client';

export default function EcoWalletPanel() {
  const { t, locale } = useI18n();
  const { colors } = useTheme();
  const [wallet, setWallet] = useState<any>(null);
  const [irrValue, setIrrValue] = useState<number>(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchWallet = async () => {
      try {
        const res = await api.get('/api/v1/wallet');
        if (res.success && res.data) {
          setWallet(res.data);
          setIrrValue(res.data.irr_equivalent || 0);
        }
      } catch (e) {
        console.error('Failed to load wallet:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchWallet();
  }, []);

  // حالت لودینگ (اسکلتون)
  if (loading) {
    return (
      <div
        style={{
          padding: '20px',
          background: colors.cardBg,
          borderRadius: '16px',
          border: `1px solid ${colors.border}`,
          minHeight: '180px',
        }}
      >
        <div
          style={{
            width: '60%',
            height: '14px',
            background: `${colors.border}66`,
            borderRadius: '8px',
            marginBottom: '12px',
          }}
        />
        <div style={{ width: '80%', height: '10px', background: `${colors.border}55`, borderRadius: '8px' }} />
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        padding: '20px',
        borderRadius: '16px',
        background: `linear-gradient(135deg, #0f766e20, #0d948820)`,
        border: `1px solid ${colors.border}`,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <h3 style={{ color: colors.text, fontSize: '1.1rem', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Wallet size={20} color={colors.primary} /> {t('eco_wallet_title')}
        </h3>
      </div>

      <div style={{ marginBottom: '16px' }}>
        <div style={{ fontSize: '0.875rem', color: colors.textMuted }}>{t('eco_balance_label')}</div>
        
        {/* ✅ رفع باگ به‌هم‌ریختگی با استفاده از Optional Chaining (?. ) و مقدار پیش‌فرض */}
        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#065f46' }}>
          {wallet?.balance?.toFixed(1) ?? '0.0'} ECO
        </div>
        
        <div style={{ fontSize: '0.875rem', color: '#047857' }}>
          ≈ {irrValue?.toLocaleString() ?? '0'} {locale === 'fa' ? 'تومان' : 'IRR'}
        </div>
      </div>

      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        <button
          style={{
            padding: '8px 12px',
            background: colors.primary,
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '0.8rem',
          }}
        >
          {t('eco_transfer')}
        </button>
        <button
          style={{
            padding: '8px 12px',
            background: 'transparent',
            color: colors.text,
            border: `1px solid ${colors.border}`,
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '0.8rem',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
        >
          {t('eco_history')} <ArrowRight size={14} />
        </button>
      </div>
    </motion.div>
  );
}