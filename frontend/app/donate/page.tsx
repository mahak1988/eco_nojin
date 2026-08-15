'use client';
import { useState } from 'react';
import Navbar from '../../components/layout/Navbar';
import Footer from '../../components/layout/Footer';
import { useI18n } from '../../lib/i18n-context';
import { useTheme } from '../../lib/theme-context';
import { useBreakpoint } from '../../lib/use-breakpoint';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Heart, Copy, Check, Wallet, Bitcoin, Gem,
  Sparkles, TreePine, Droplet, Users, HandHeart,
  Globe, Shield, Star
} from 'lucide-react';

// Public donation addresses (REPLACE WITH YOUR REAL ADDRESSES)
const wallets = [
  {
    id: 'usdt-erc20',
    name: 'USDT (ERC-20)',
    network: 'Ethereum',
    address: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0', // REPLACE
    icon: '💵',
    color: '#26a17b',
    description: {
      en: 'Tether on Ethereum network (stable, widely accepted)',
      fa: 'تتر بر شبکه اتریوم (پایدار، پرکاربرد)',
    },
  },
  {
    id: 'usdt-trc20',
    name: 'USDT (TRC-20)',
    network: 'Tron',
    address: 'TJXxqXvZqY4y6p7C4rFqM2KqJwQ3VcXnDp', // REPLACE
    icon: '💵',
    color: '#eb0029',
    description: {
      en: 'Tether on Tron network (low fees)',
      fa: 'تتر بر شبکه ترون (کارمزد پایین)',
    },
  },
  {
    id: 'btc',
    name: 'Bitcoin (BTC)',
    network: 'Bitcoin',
    address: 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh', // REPLACE
    icon: '₿',
    color: '#f7931a',
    description: {
      en: 'Bitcoin - the original cryptocurrency',
      fa: 'بیت‌کوین - اولین رمزارز جهان',
    },
  },
  {
    id: 'eth',
    name: 'Ethereum (ETH)',
    network: 'Ethereum',
    address: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1', // REPLACE
    icon: '⟠',
    color: '#627eea',
    description: {
      en: 'Ethereum - for smart contract-based donations',
      fa: 'اتریوم - برای اهداهای مبتنی بر قراردادهای هوشمند',
    },
  },
  {
    id: 'matic',
    name: 'Polygon (MATIC)',
    network: 'Polygon',
    address: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb2', // REPLACE
    icon: '💠',
    color: '#8247e5',
    description: {
      en: 'Polygon - eco-friendly, very low fees',
      fa: 'پلیگان - دوستدار محیط زیست، کارمزد بسیار پایین',
    },
  },
];

const impactTiers = [
  { amount: '10', impact: { en: 'Plants 5 native trees', fa: 'کاشت ۵ درخت بومی' }, icon: TreePine, color: '#16a34a' },
  { amount: '50', impact: { en: 'Restores 50m² of degraded soil', fa: 'احیای ۵۰ مترمربع خاک تخریب‌شده' }, icon: Sprout, color: '#f97316' },
  { amount: '100', impact: { en: 'Provides clean water for 1 family/year', fa: 'تامین آب پاک برای ۱ خانواده/سال' }, icon: Droplet, color: '#0ea5e9' },
  { amount: '500', impact: { en: 'Trains 10 farmers in CSA', fa: 'آموزش ۱۰ کشاورز در CSA' }, icon: Users, color: '#fbbf24' },
  { amount: '1000', impact: { en: 'Restores 1 hectare of landscape', fa: 'احیای ۱ هکتار منظر' }, icon: Globe, color: '#fb7185' },
];

import { Sprout } from 'lucide-react';

export default function DonatePage() {
  const { t, direction, locale } = useI18n();
  const { colors, theme } = useTheme();
  const { isMobile } = useBreakpoint();
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [toastVisible, setToastVisible] = useState(false);

  const handleCopy = async (id: string, address: string) => {
    try {
      await navigator.clipboard.writeText(address);
      setCopiedId(id);
      setToastVisible(true);
      setTimeout(() => {
        setCopiedId(null);
        setToastVisible(false);
      }, 2500);
    } catch (err) {
      console.error('Copy failed', err);
    }
  };

  const getLocalized = (obj: any) => obj[locale] || obj.en || Object.values(obj)[0];

  return (
    <div dir={direction} style={{ background: colors.bg, minHeight: '100vh', position: 'relative' }}>
      <Navbar />

      {/* Success Toast */}
      <AnimatePresence>
        {toastVisible && (
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.8 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 50, scale: 0.8 }}
            style={{
              position: 'fixed',
              bottom: '32px',
              left: '50%',
              transform: 'translateX(-50%)',
              background: `linear-gradient(135deg, ${colors.success}, ${colors.calm})`,
              color: 'white',
              padding: '16px 28px',
              borderRadius: '14px',
              boxShadow: '0 16px 48px rgba(0,0,0,0.2)',
              zIndex: 2000,
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              fontWeight: '600',
              fontSize: '0.95rem',
            }}
          >
            <Check size={20} />
            {t('donate_copy_success')}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Hero */}
      <section style={{
        padding: isMobile ? '80px 20px 60px' : '120px 48px 80px',
        background: theme === 'dark'
          ? 'radial-gradient(ellipse at top, rgba(251, 113, 133, 0.2), transparent 60%), #0c0a09'
          : 'radial-gradient(ellipse at top, rgba(251, 113, 133, 0.15), transparent 60%), #fffbeb',
        position: 'relative',
        overflow: 'hidden',
      }}>
        <motion.div
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ duration: 4, repeat: Infinity }}
          style={{
            position: 'absolute', top: '20%', left: '50%',
            transform: 'translateX(-50%)',
            width: '500px', height: '500px',
            background: 'radial-gradient(circle, rgba(251, 113, 133, 0.2), transparent 70%)',
            borderRadius: '50%', filter: 'blur(60px)', pointerEvents: 'none',
          }}
        />

        <div style={{ maxWidth: '900px', margin: '0 auto', textAlign: 'center', position: 'relative', zIndex: 1 }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ marginBottom: '24px' }}
          >
            <motion.div
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              style={{
                width: '80px', height: '80px',
                borderRadius: '50%',
                background: `linear-gradient(135deg, ${colors.primary}, #fb7185)`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                margin: '0 auto 24px',
                boxShadow: `0 16px 48px ${colors.primary}50`,
              }}
            >
              <Heart size={40} color="white" fill="white" strokeWidth={0} />
            </motion.div>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            style={{
              fontSize: isMobile ? '2.25rem' : '3.5rem',
              fontWeight: '800', lineHeight: 1.1,
              marginBottom: '20px',
            }}
          >
            <span className="love-gradient-text">{t('donate_title')}</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            style={{
              fontSize: isMobile ? '1rem' : '1.2rem',
              color: colors.textMuted, maxWidth: '700px',
              margin: '0 auto', lineHeight: 1.7,
            }}
          >
            {t('donate_subtitle')}
          </motion.p>
        </div>
      </section>

      {/* Impact Tiers */}
      <section style={{ padding: isMobile ? '40px 20px 60px' : '60px 48px 80px', background: colors.bg }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            style={{ textAlign: 'center', marginBottom: '40px' }}
          >
            <div style={{
              display: 'inline-block',
              padding: '6px 16px',
              background: `${colors.primary}15`,
              color: colors.primary,
              borderRadius: '100px',
              fontSize: '0.875rem', fontWeight: '600',
              marginBottom: '16px',
            }}>
              🌱 Your Impact
            </div>
            <h2 style={{ fontSize: isMobile ? '1.5rem' : '2rem', fontWeight: '800', color: colors.text, marginBottom: '12px' }}>
              What Your Donation Does
            </h2>
            <p style={{ fontSize: '1rem', color: colors.textMuted }}>
              Every dollar creates measurable, verifiable impact
            </p>
          </motion.div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '16px',
          }}>
            {impactTiers.map((tier, i) => {
              const Icon = tier.icon;
              return (
                <motion.div
                  key={tier.amount}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.05 }}
                  whileHover={{ y: -6 }}
                  style={{
                    background: colors.cardBg,
                    backdropFilter: 'blur(20px)',
                    border: `1px solid ${colors.border}`,
                    padding: '24px 16px',
                    borderRadius: '16px',
                    textAlign: 'center',
                  }}
                >
                  <div style={{
                    width: '48px', height: '48px',
                    borderRadius: '12px',
                    background: `${tier.color}20`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    margin: '0 auto 12px',
                    border: `2px solid ${tier.color}30`,
                  }}>
                    <Icon size={24} color={tier.color} strokeWidth={2.5} />
                  </div>
                  <div style={{ fontSize: '1.75rem', fontWeight: '800', color: tier.color, marginBottom: '8px' }}>
                    ${tier.amount}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: colors.text, lineHeight: 1.5 }}>
                    {getLocalized(tier.impact)}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Wallet Addresses */}
      <section style={{
        padding: isMobile ? '40px 20px 60px' : '60px 48px 80px',
        background: theme === 'dark'
          ? 'linear-gradient(180deg, #1c1917 0%, #0c0a09 100%)'
          : 'linear-gradient(180deg, #fef3c7 0%, #fffbeb 100%)',
      }}>
        <div style={{ maxWidth: '900px', margin: '0 auto' }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            style={{ textAlign: 'center', marginBottom: '40px' }}
          >
            <div style={{
              display: 'inline-block',
              padding: '6px 16px',
              background: `${colors.accent}15`,
              color: colors.accent,
              borderRadius: '100px',
              fontSize: '0.875rem', fontWeight: '600',
              marginBottom: '16px',
            }}>
              💝 Donate with Crypto
            </div>
            <h2 style={{ fontSize: isMobile ? '1.5rem' : '2rem', fontWeight: '800', color: colors.text, marginBottom: '12px' }}>
              Cryptocurrency Wallets
            </h2>
            <p style={{ fontSize: '1rem', color: colors.textMuted }}>
              Click any address to copy. Verify the address on your wallet before sending.
            </p>
          </motion.div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {wallets.map((wallet, i) => (
              <motion.div
                key={wallet.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05 }}
                style={{
                  background: colors.cardBg,
                  backdropFilter: 'blur(20px)',
                  border: `1px solid ${colors.border}`,
                  borderRadius: '16px',
                  padding: '24px',
                  transition: 'all 0.3s',
                }}
                whileHover={{ boxShadow: `0 12px 32px ${wallet.color}20` }}
              >
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  marginBottom: '16px',
                  flexWrap: 'wrap',
                }}>
                  <div style={{
                    width: '44px', height: '44px',
                    borderRadius: '12px',
                    background: `${wallet.color}20`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '1.5rem',
                    border: `2px solid ${wallet.color}40`,
                    flexShrink: 0,
                  }}>
                    {wallet.icon}
                  </div>
                  <div style={{ flex: 1, minWidth: '150px' }}>
                    <div style={{ fontWeight: '700', color: colors.text, fontSize: '1.05rem' }}>
                      {wallet.name}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: colors.textMuted }}>
                      {wallet.network}
                    </div>
                  </div>
                  <div style={{
                    padding: '4px 12px',
                    background: `${wallet.color}15`,
                    color: wallet.color,
                    borderRadius: '100px',
                    fontSize: '0.75rem',
                    fontWeight: '600',
                  }}>
                    {wallet.network}
                  </div>
                </div>

                <div style={{
                  fontSize: '0.85rem',
                  color: colors.textMuted,
                  marginBottom: '12px',
                  lineHeight: 1.5,
                }}>
                  {getLocalized(wallet.description)}
                </div>

                <div style={{
                  display: 'flex',
                  gap: '8px',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                }}>
                  <div style={{
                    flex: 1,
                    minWidth: 0,
                    padding: '12px 14px',
                    background: colors.bg,
                    border: `1px solid ${colors.border}`,
                    borderRadius: '10px',
                    fontFamily: 'monospace',
                    fontSize: isMobile ? '0.75rem' : '0.85rem',
                    color: colors.text,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}>
                    {wallet.address}
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => handleCopy(wallet.id, wallet.address)}
                    style={{
                      padding: '12px 20px',
                      background: copiedId === wallet.id
                        ? `linear-gradient(135deg, ${colors.success}, ${colors.calm})`
                        : `linear-gradient(135deg, ${wallet.color}, ${colors.primary})`,
                      color: 'white',
                      border: 'none',
                      borderRadius: '10px',
                      fontWeight: '600',
                      fontSize: '0.875rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      boxShadow: `0 4px 12px ${wallet.color}40`,
                      flexShrink: 0,
                    }}
                  >
                    {copiedId === wallet.id ? (
                      <>
                        <Check size={16} />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy size={16} />
                        {t('donate_copy_button')}
                      </>
                    )}
                  </motion.button>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Warning */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            style={{
              marginTop: '24px',
              padding: '16px 20px',
              background: `${colors.warning}15`,
              border: `1px solid ${colors.warning}30`,
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px',
            }}
          >
            <Shield size={20} color={colors.warning} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div style={{ fontSize: '0.875rem', color: colors.text, lineHeight: 1.6 }}>
              <strong style={{ color: colors.warning }}>Security reminder:</strong> Always
              verify the wallet address on this official page before sending. Cryptocurrency
              transactions are irreversible. Hydroma Nojin will never contact you privately
              asking for donations.
            </div>
          </motion.div>
        </div>
      </section>

      {/* Why Support Us */}
      <section style={{ padding: isMobile ? '60px 20px' : '80px 48px', background: colors.bg }}>
        <div style={{ maxWidth: '900px', margin: '0 auto' }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            style={{ textAlign: 'center', marginBottom: '48px' }}
          >
            <h2 style={{ fontSize: isMobile ? '1.75rem' : '2.25rem', fontWeight: '800', color: colors.text, marginBottom: '16px' }}>
              Where Your Support Goes
            </h2>
            <p style={{ fontSize: '1.1rem', color: colors.textMuted }}>
              100% transparent. 100% impact-focused.
            </p>
          </motion.div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '20px',
          }}>
            {[
              {
                icon: TreePine,
                title: 'Land Restoration',
                desc: 'Directly funds biological terraces, infiltration pits, and native tree planting in degraded landscapes.',
                color: '#16a34a',
              },
              {
                icon: Users,
                title: 'Farmer Empowerment',
                desc: 'Trains smallholder farmers in climate-smart agriculture and supports cooperatives.',
                color: '#f97316',
              },
              {
                icon: HandHeart,
                title: 'Rural Livelihoods',
                desc: 'Creates alternative income sources: medicinal plants, beekeeping, local processing.',
                color: '#fb7185',
              },
              {
                icon: Star,
                title: 'Open Science',
                desc: 'Keeps our platform free for the poorest farmers and our research openly published.',
                color: '#fbbf24',
              },
            ].map((item, i) => {
              const Icon = item.icon;
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.08 }}
                  style={{
                    background: colors.cardBg,
                    backdropFilter: 'blur(20px)',
                    border: `1px solid ${colors.border}`,
                    padding: '24px',
                    borderRadius: '16px',
                    textAlign: 'center',
                  }}
                >
                  <div style={{
                    width: '52px', height: '52px',
                    borderRadius: '14px',
                    background: `${item.color}20`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    margin: '0 auto 16px',
                    border: `2px solid ${item.color}30`,
                  }}>
                    <Icon size={26} color={item.color} strokeWidth={2.5} />
                  </div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: colors.text, marginBottom: '8px' }}>
                    {item.title}
                  </h3>
                  <p style={{ fontSize: '0.875rem', color: colors.textMuted, lineHeight: 1.6 }}>
                    {item.desc}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Thank You */}
      <section style={{
        padding: isMobile ? '60px 20px' : '80px 48px',
        background: `linear-gradient(135deg, ${colors.primary} 0%, #fb7185 50%, ${colors.accent} 100%)`,
        textAlign: 'center',
        color: 'white',
        position: 'relative',
        overflow: 'hidden',
      }}>
        <motion.div
          animate={{ y: [0, -10, 0] }}
          transition={{ duration: 4, repeat: Infinity }}
          style={{
            position: 'absolute', top: '50%', left: '10%',
            width: '200px', height: '200px',
            background: 'radial-gradient(circle, rgba(255,255,255,0.15), transparent 70%)',
            borderRadius: '50%', pointerEvents: 'none',
          }}
        />
        <div style={{ position: 'relative', zIndex: 1, maxWidth: '700px', margin: '0 auto' }}>
          <Heart size={56} fill="white" color="white" style={{ marginBottom: '20px' }} />
          <h2 style={{ fontSize: isMobile ? '1.75rem' : '2.5rem', fontWeight: '800', marginBottom: '16px' }}>
            Thank You
          </h2>
          <p style={{ fontSize: '1.15rem', opacity: 0.95, lineHeight: 1.7 }}>
            Every act of generosity is a seed of hope. Whether you give $10 or $10,000,
            whether you share knowledge or time—you are part of the restoration of our
            shared home.
          </p>
          <p style={{ fontSize: '1rem', marginTop: '24px', fontStyle: 'italic', opacity: 0.9 }}>
            "The earth is what we all have in common." — Wendell Berry
          </p>
        </div>
      </section>

      <Footer />
    </div>
  );
}
