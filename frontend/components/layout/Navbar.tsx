'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { useI18n } from '../../lib/i18n-context';
import { useTheme } from '../../lib/theme-context';
import { useBreakpoint } from '../../lib/use-breakpoint';
import ThemeToggle from '../shared/ThemeToggle';
import MobileMenu from './MobileMenu';
import { motion } from 'framer-motion';
import { DollarSign, Globe, HandHeart, Home, Info, Layout, LayoutDashboard, Leaf, LogIn, Mail, Menu, UserPlus , Bot , Wallet, BarChart3 } from 'lucide-react';

export default function Navbar() {
  const { t, locale, setLocale } = useI18n();
  const { colors } = useTheme();
  const pathname = usePathname();
  const { isMobile, isTablet } = useBreakpoint();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const isSmallScreen = isMobile || isTablet;

  const links = [
    { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/modules/ecowallet', label: 'EcoWallet', icon: Wallet },
    { href: '/modules/analytics', label: 'Analytics', icon: BarChart3 },
    { href: '/', label: t('nav_home'), icon: Home },
    { href: '/pricing', label: t('nav_pricing'), icon: DollarSign },
    { href: '/about', label: t('nav_about'), icon: Info },
    { href: '/modules/ai', label: 'AI Assistant', icon: Bot },
    { href: '/contact', label: t('nav_contact'), icon: Mail },
    { href: '/mission', label: t('nav_mission'), icon: Globe },
    { href: '/donate', label: t('nav_donate'), icon: HandHeart },
  ];

  const languages = [
    { code: 'en', name: 'EN', flag: '🇺🇸' },
    { code: 'fa', name: 'فا', flag: '🇮🇷' },
    { code: 'ar', name: 'عر', flag: '🇸🇦' },
    { code: 'fr', name: 'FR', flag: '🇫🇷' },
    { code: 'es', name: 'ES', flag: '🇪🇸' },
  ];

  return (
    <>
      <motion.nav
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5 }}
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: isSmallScreen ? '12px 16px' : '12px 48px',
          gap: isSmallScreen ? '8px' : '16px',
          background: colors.glass,
          backdropFilter: 'blur(20px) saturate(180%)',
          WebkitBackdropFilter: 'blur(20px) saturate(180%)',
          borderBottom: `1px solid ${colors.border}`,
          position: 'sticky',
          top: 0,
          zIndex: 1000,
        }}
      >
        {/* Logo */}
        <Link href="/" style={{
          display: 'flex', alignItems: 'center', gap: '10px',
          fontSize: isSmallScreen ? '1.2rem' : '1.4rem',
          fontWeight: '700',
          flexShrink: 0,
        }}>
          <motion.div
            whileHover={{ rotate: 360, scale: 1.1 }}
            transition={{ duration: 0.6 }}
            style={{
              width: isSmallScreen ? '36px' : '42px',
              height: isSmallScreen ? '36px' : '42px',
              borderRadius: '12px',
              background: `linear-gradient(135deg, ${colors.primaryLight}, ${colors.accent})`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)',
              flexShrink: 0,
            }}
          >
            <Leaf size={isSmallScreen ? 18 : 22} color="white" strokeWidth={2.5} />
          </motion.div>
          <span className="gradient-text" style={{ display: isMobile ? 'none' : 'inline' }}>Eco Nojin</span>
        </Link>

        {/* Desktop Links */}
        {!isSmallScreen && (
          <div style={{ display: 'flex', gap: '4px', alignItems: 'center', flex: 1, justifyContent: 'center' }}>
            {links.map(link => {
              const isActive = pathname === link.href ||
                              (link.href !== '/' && pathname.startsWith(link.href));
              const Icon = link.icon;
              return (
                <Link key={link.href} href={link.href}>
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.98 }}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '6px',
                      padding: '8px 14px', borderRadius: '10px',
                      fontSize: '0.9rem', fontWeight: '500',
                      background: isActive ? `${colors.primaryLight}20` : 'transparent',
                      color: isActive ? colors.primary : colors.text,
                      transition: 'all 0.2s', cursor: 'pointer',
                    }}
                  >
                    <Icon size={16} />
                    <span>{link.label}</span>
                  </motion.div>
                </Link>
              );
            })}
          </div>
        )}

        {/* Right section */}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexShrink: 0 }}>
          <ThemeToggle />

          {!isSmallScreen && (
            <>
              <select
                value={locale}
                onChange={(e) => setLocale(e.target.value)}
                style={{
                  padding: '8px 12px', borderRadius: '10px',
                  border: `1px solid ${colors.border}`,
                  background: colors.cardBg, color: colors.text,
                  fontSize: '0.875rem', cursor: 'pointer',
                }}
              >
                {languages.map(l => (
                  <option key={l.code} value={l.code}>{l.flag} {l.name}</option>
                ))}
              </select>

              <Link href="/login">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  style={{
                    padding: '8px 18px',
                    background: 'transparent',
                    color: colors.primary,
                    border: `1.5px solid ${colors.primary}`,
                    borderRadius: '10px',
                    fontSize: '0.9rem', fontWeight: '600',
                    display: 'flex', alignItems: 'center', gap: '6px',
                    cursor: 'pointer',
                  }}
                >
                  <LogIn size={16} />
                  {t('nav_login')}
                </motion.button>
              </Link>

              <Link href="/register">
                <motion.button
                  whileHover={{ scale: 1.05, boxShadow: '0 8px 24px rgba(16, 185, 129, 0.4)' }}
                  whileTap={{ scale: 0.95 }}
                  style={{
                    padding: '8px 18px',
                    background: `linear-gradient(135deg, ${colors.primaryLight}, ${colors.primary})`,
                    color: 'white', border: 'none', borderRadius: '10px',
                    fontSize: '0.9rem', fontWeight: '600',
                    display: 'flex', alignItems: 'center', gap: '6px',
                    cursor: 'pointer',
                    boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)',
                  }}
                >
                  <UserPlus size={16} />
                  {t('nav_register')}
                </motion.button>
              </Link>
            </>
          )}

          {/* Mobile Hamburger */}
          {isSmallScreen && (
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={() => setMobileMenuOpen(true)}
              style={{
                width: '40px', height: '40px',
                borderRadius: '10px',
                border: `1px solid ${colors.border}`,
                background: colors.cardBg,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                cursor: 'pointer',
              }}
              aria-label="Open menu"
            >
              <Menu size={20} color={colors.text} />
            </motion.button>
          )}
        </div>
      </motion.nav>

      {/* Mobile Menu */}
      <MobileMenu isOpen={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} />
    </>
  );
}
