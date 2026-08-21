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
import {
  BookOpen, FlaskConical, Globe, Home, Info, LayoutDashboard, Leaf, LogIn, Menu, UserPlus
} from 'lucide-react';
import LanguageSwitcher from '../LanguageSwitcher';

export default function Navbar() {
  const { t } = useI18n();
  const { colors } = useTheme();
  const pathname = usePathname();
  const { isMobile, isTablet } = useBreakpoint();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const isSmallScreen = isMobile || isTablet;

  const links = [
    { href: '/', label: t('nav_home'), icon: Home },
    { href: '/dashboard', label: 'داشبورد', icon: LayoutDashboard },
    { href: '/modules', label: 'ماژول‌ها', icon: FlaskConical },
    { href: '/science', label: 'مرکز علم', icon: BookOpen },
    { href: '/models', label: 'مدل‌ها', icon: FlaskConical },
    { href: '/mission', label: t('nav_mission'), icon: Globe },
    { href: '/about', label: t('nav_about'), icon: Info },
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
          <span style={{ display: isMobile ? 'none' : 'inline', color: colors.text }}>Eco Nojin</span>
        </Link>

        {/* Desktop Links with Gradient Underline */}
        {!isSmallScreen && (
          <div style={{ display: 'flex', gap: '4px', alignItems: 'center', flex: 1, justifyContent: 'center' }}>
            {links.map(link => {
              const isActive = pathname === link.href || (link.href !== '/' && pathname.startsWith(link.href));
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
                      color: isActive ? colors.primary : colors.text,
                      cursor: 'pointer',
                      position: 'relative',
                      transition: 'color 0.2s ease',
                    }}
                  >
                    <Icon size={16} color={isActive ? colors.primary : colors.textMuted} />
                    <span>{link.label}</span>

                    {/* خط زیرین ثابت برای لینک فعال */}
                    {isActive && (
                      <motion.div
                        layoutId="activeNavUnderline"
                        transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                        style={{
                          position: 'absolute',
                          bottom: 2, left: 14, right: 14,
                          height: '2px',
                          background: colors.primary,
                          borderRadius: '2px',
                        }}
                      />
                    )}

                    {/* خط زیرین گرادیانت انیمیشن‌دار برای حالت هاور (فقط زمانی که فعال نیست) */}
                    {!isActive && (
                      <motion.div
                        initial={{ width: 0 }}
                        whileHover={{ width: 'calc(100% - 28px)' }}
                        transition={{ duration: 0.25 }}
                        style={{
                          position: 'absolute',
                          bottom: 2, left: 14,
                          height: '2px',
                          background: `linear-gradient(90deg, ${colors.primary}, transparent)`,
                          borderRadius: '2px',
                        }}
                      />
                    )}
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
              <LanguageSwitcher />

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
                    transition: 'all 0.2s ease',
                  }}
                >
                  <LogIn size={16} />
                  {t('nav_login')}
                </motion.button>
              </Link>

              <Link href="/register">
                <motion.button
                  whileHover={{ scale: 1.05, boxShadow: `0 8px 24px ${colors.primary}50` }}
                  whileTap={{ scale: 0.95 }}
                  style={{
                    padding: '8px 18px',
                    background: `linear-gradient(135deg, ${colors.primaryLight}, ${colors.primary})`,
                    color: 'white', border: 'none', borderRadius: '10px',
                    fontSize: '0.9rem', fontWeight: '600',
                    display: 'flex', alignItems: 'center', gap: '6px',
                    cursor: 'pointer',
                    boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)',
                    transition: 'all 0.2s ease',
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