'use client';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { useI18n } from '../../lib/i18n-context';
import { useTheme } from '../../lib/theme-context';
import {
  Home, Layout, DollarSign, Info, Mail,
  LogIn, UserPlus, X, Leaf
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
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0,0,0,0.5)',
              backdropFilter: 'blur(4px)',
              zIndex: 1100,
            }}
          />

          {/* Menu Panel */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            style={{
              position: 'fixed',
              top: 0,
              right: 0,
              bottom: 0,
              width: 'min(320px, 85vw)',
              background: colors.bgAlt,
              zIndex: 1200,
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '-4px 0 24px rgba(0,0,0,0.1)',
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
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{
                  width: '36px', height: '36px', borderRadius: '10px',
                  background: `linear-gradient(135deg, ${colors.primaryLight}, ${colors.accent})`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <Leaf size={18} color="white" strokeWidth={2.5} />
                </div>
                <span style={{ fontWeight: '700', color: colors.text }}>Eco Nojin</span>
              </div>
              <motion.button
                whileTap={{ scale: 0.9 }}
                onClick={onClose}
                style={{
                  width: '36px', height: '36px',
                  borderRadius: '8px',
                  border: `1px solid ${colors.border}`,
                  background: colors.bg,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  cursor: 'pointer',
                }}
              >
                <X size={18} color={colors.text} />
              </motion.button>
            </div>

            {/* Navigation */}
            <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {links.map(link => {
                const Icon = link.icon;
                return (
                  <Link key={link.href} href={link.href} onClick={onClose}>
                    <motion.div
                      whileTap={{ scale: 0.98 }}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '14px',
                        padding: '14px 16px',
                        borderRadius: '10px',
                        color: colors.text,
                        fontSize: '0.95rem',
                        fontWeight: '500',
                        transition: 'background 0.2s',
                      }}
                      onMouseOver={(e) => (e.currentTarget.style.background = `${colors.primaryLight}15`)}
                      onMouseOut={(e) => (e.currentTarget.style.background = 'transparent')}
                    >
                      <Icon size={20} color={colors.primary} />
                      <span>{link.label}</span>
                    </motion.div>
                  </Link>
                );
              })}
            </nav>

            {/* Language */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{
                fontSize: '0.75rem', color: colors.textMuted,
                textTransform: 'uppercase', letterSpacing: '1px',
                marginBottom: '8px',
              }}>
                Language
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
                      padding: '10px 8px',
                      borderRadius: '8px',
                      border: locale === l.code ? `2px solid ${colors.primary}` : `1px solid ${colors.border}`,
                      background: locale === l.code ? `${colors.primaryLight}15` : colors.bg,
                      color: colors.text,
                      fontSize: '0.8rem',
                      cursor: 'pointer',
                      fontWeight: locale === l.code ? '600' : '400',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <span style={{ fontSize: '1.25rem' }}>{l.flag}</span>
                    <span>{l.name}</span>
                  </motion.button>
                ))}
              </div>
            </div>

            {/* Auth buttons */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <Link href="/login" onClick={onClose}>
                <motion.button
                  whileTap={{ scale: 0.98 }}
                  style={{
                    width: '100%',
                    padding: '12px',
                    borderRadius: '10px',
                    border: `1.5px solid ${colors.primary}`,
                    background: 'transparent',
                    color: colors.primary,
                    fontWeight: '600',
                    fontSize: '0.95rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                  }}
                >
                  <LogIn size={18} />
                  {t('nav_login')}
                </motion.button>
              </Link>
              <Link href="/register" onClick={onClose}>
                <motion.button
                  whileTap={{ scale: 0.98 }}
                  style={{
                    width: '100%',
                    padding: '12px',
                    borderRadius: '10px',
                    border: 'none',
                    background: `linear-gradient(135deg, ${colors.primaryLight}, ${colors.primary})`,
                    color: 'white',
                    fontWeight: '600',
                    fontSize: '0.95rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)',
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
