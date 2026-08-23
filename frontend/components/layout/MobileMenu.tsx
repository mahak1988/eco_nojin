'use client';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { useI18n } from '../../lib/i18n-context';
import { useTheme } from '../../lib/theme-context';
import {
  Home, Layout, DollarSign, Info, Mail,
  LogIn, UserPlus, X, Leaf, Wallet, Bot
} from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export default function MobileMenu({ isOpen, onClose }: Props) {
  const { t, locale, setLocale } = useI18n();
  const { colors } = useTheme();

  const links = [
    { href: '/', label: t('nav_home'), icon: Home },
    { href: '/dashboard', label: t('nav_modules'), icon: Layout },
    { href: '/tools/ai-assistant', label: t('nav_ai_tools'), icon: Bot }, // New link
    { href: '/ecowallet', label: t('nav_ecowallet'), icon: Wallet }, // New link
    { href: '/pricing', label: t('nav_pricing'), icon: DollarSign },
    { href: '/about', label: t('nav_about'), icon: Info },
    { href: '/contact', label: t('nav_contact'), icon: Mail },
  ];

  const languages = [
    { code: 'en', name: 'English', flag: '🇺🇸' },
    { code: 'fa', name: 'فارسی', flag: '🇮🇷' },
    { code: 'ar', name: 'العربية', flag: '🇸🇦' },
    { code: 'fr', name: 'Français', flag: '🇫🇷' },
    { code: 'es', name: 'Español', flag: '🇪🇸' },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop با انیمیشن محو شدن */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0,0,0,0.6)',
              backdropFilter: 'blur(8px)',
              zIndex: 1100,
            }}
          />

          {/* Menu Panel با افکت شیشه‌ای */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 250 }}
            style={{
              position: 'fixed',
              top: 0,
              right: 0,
              bottom: 0,
              width: 'min(340px, 85vw)',
              background: colors.bgAlt + 'cc', // استفاده از پس‌زمینه با شفافیت
              backdropFilter: 'blur(20px)',
              borderLeft: `1px solid ${colors.border}`,
              zIndex: 1200,
              padding: '28px 24px',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '-8px 0 40px rgba(0,0,0,0.15)',
              overflowY: 'auto',
            }}
          >
            {/* Header */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '32px',
              paddingBottom: '16px',
              borderBottom: `1px solid ${colors.border}`,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '40px', height: '40px', borderRadius: '12px',
                  background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  boxShadow: `0 4px 12px ${colors.primary}40`,
                }}>
                  <Leaf size={20} color="white" strokeWidth={2.5} />
                </div>
                <span style={{ fontWeight: '700', fontSize: '1.2rem', color: colors.text }}>Eco Nojin</span>
              </div>
              <motion.button
                whileTap={{ scale: 0.9 }}
                onClick={onClose}
                style={{
                  width: '40px', height: '40px',
                  borderRadius: '12px',
                  border: `1px solid ${colors.border}`,
                  background: colors.bg,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  cursor: 'pointer',
                  color: colors.text,
                  transition: 'all 0.2s',
                }}
              >
                <X size={20} />
              </motion.button>
            </div>

            {/* Navigation */}
            <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {links.map(link => {
                const Icon = link.icon;
                return (
                  <Link key={link.href} href={link.href} onClick={onClose}>
                    <motion.div
                      whileTap={{ scale: 0.97 }}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '16px',
                        padding: '14px 18px',
                        borderRadius: '12px',
                        color: colors.text,
                        fontSize: '0.95rem',
                        fontWeight: '500',
                        cursor: 'pointer',
                        position: 'relative',
                        transition: 'background 0.2s ease',
                      }}
                      onMouseOver={(e) => {
                        e.currentTarget.style.background = `${colors.primary}15`;
                      }}
                      onMouseOut={(e) => {
                        e.currentTarget.style.background = 'transparent';
                      }}
                    >
                      <Icon size={20} color={colors.primary} />
                      <span>{link.label}</span>
                      
                      {/* خط زیرین ظریف هنگام هاور (اختیاری برای زیبایی) */}
                      <motion.div
                        initial={{ width: 0 }}
                        whileHover={{ width: '30%' }}
                        transition={{ duration: 0.2 }}
                        style={{
                          position: 'absolute',
                          bottom: 6, left: 18,
                          height: '2px',
                          background: `linear-gradient(90deg, ${colors.primary}, transparent)`,
                          borderRadius: '2px',
                        }}
                      />
                    </motion.div>
                  </Link>
                );
              })}
            </nav>

            {/* Language Selector */}
            <div style={{ marginTop: 'auto', marginBottom: '20px' }}>
              <div style={{
                fontSize: '0.75rem', color: colors.textMuted,
                textTransform: 'uppercase', letterSpacing: '0.5px',
                marginBottom: '12px', paddingLeft: '6px',
              }}>
                زبان / Language
              </div>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(80px, 1fr))',
                gap: '8px',
              }}>
                {languages.map(l => (
                  <motion.button
                    key={l.code}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => { setLocale(l.code); }}
                    style={{
                      padding: '10px 6px',
                      borderRadius: '10px',
                      border: locale === l.code 
                        ? `2px solid ${colors.primary}` 
                        : `1px solid ${colors.border}`,
                      background: locale === l.code 
                        ? `${colors.primary}20` 
                        : 'transparent',
                      color: colors.text,
                      fontSize: '0.75rem',
                      cursor: 'pointer',
                      fontWeight: locale === l.code ? '600' : '400',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '4px',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <span style={{ fontSize: '1.2rem' }}>{l.flag}</span>
                    <span>{l.name}</span>
                  </motion.button>
                ))}
              </div>
            </div>

            {/* Auth buttons */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <Link href="/login" onClick={onClose}>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.97 }}
                  style={{
                    width: '100%',
                    padding: '14px',
                    borderRadius: '12px',
                    border: `1.5px solid ${colors.primary}`,
                    background: 'transparent',
                    color: colors.primary,
                    fontWeight: '600',
                    fontSize: '0.95rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '10px',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <LogIn size={18} />
                  {t('nav_login')}
                </motion.button>
              </Link>
              
              <Link href="/register" onClick={onClose}>
                <motion.button
                  whileHover={{ scale: 1.02, boxShadow: `0 8px 24px ${colors.primary}40` }}
                  whileTap={{ scale: 0.97 }}
                  style={{
                    width: '100%',
                    padding: '14px',
                    borderRadius: '12px',
                    border: 'none',
                    background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
                    color: 'white',
                    fontWeight: '600',
                    fontSize: '0.95rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '10px',
                  }}
                >
                  <UserPlus size={18} />
                  {t('nav_register')}
                </motion.button>
              </Link>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}