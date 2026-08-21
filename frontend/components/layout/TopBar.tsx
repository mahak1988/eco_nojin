'use client';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { useI18n } from '../../lib/i18n-context';
import { useTheme } from '../../lib/theme-context';
import { useBreakpoint } from '../../lib/use-breakpoint';
import ThemeToggle from '../shared/ThemeToggle';
import LanguageSwitcher from '../LanguageSwitcher';
import { Bell, Search } from 'lucide-react';

export default function TopBar({ compact = false }: { compact?: boolean }) {
  const { t, locale } = useI18n();
  const { colors } = useTheme();
  const { isMobile, isTablet } = useBreakpoint();
  const isSmall = compact || isMobile || isTablet;

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: isSmall ? '8px 12px' : '12px 24px',
      gap: '8px',
      background: colors.cardBg,
      backdropFilter: 'blur(20px)',
      borderBottom: compact ? 'none' : `1px solid ${colors.border}`,
      width: '100%',
    }}>
      {/* Search (hide on very small) */}
      {!isMobile && !compact && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: '8px',
          padding: '8px 14px', borderRadius: '10px',
          background: colors.bg,
          border: `1px solid ${colors.border}`,
          flex: 1, maxWidth: '400px',
          transition: 'border-color 0.3s ease',
        }}>
          <Search size={16} color={colors.textMuted} />
          <input
            type="text"
            aria-label={t('topbar_search')} placeholder={t('topbar_search')}
            style={{
              border: 'none', outline: 'none',
              background: 'transparent', flex: 1,
              fontSize: '0.875rem', color: colors.text,
              fontFamily: 'inherit',
              width: '100%',
            }}
            // افکت فوکوس با خط زیرین گرادیانت
            onFocus={(e) => {
              e.currentTarget.parentElement!.style.borderColor = colors.primary;
            }}
            onBlur={(e) => {
              e.currentTarget.parentElement!.style.borderColor = colors.border;
            }}
          />
        </div>
      )}

      <div style={{ flex: isMobile ? 1 : 'none' }} />

      {/* Right actions */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: isSmall ? '6px' : '10px',
        flexShrink: 0,
      }}>
        {!compact && (
          <motion.div
            whileHover={{ rotate: [0, -10, 10, -5, 5, 0], scale: 1.1 }}
            transition={{ duration: 0.5 }}
            whileTap={{ scale: 0.95 }}
            style={{
              width: '40px', height: '40px',
              borderRadius: '10px',
              background: colors.bg,
              border: `1px solid ${colors.border}`,
              display: 'flex', alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              position: 'relative',
            }}
          >
            <Bell size={18} color={colors.text} />
            <span style={{
              position: 'absolute',
              top: '-4px', right: '-4px',
              background: '#ef4444', color: 'white',
              fontSize: '0.7rem', fontWeight: 'bold',
              borderRadius: '50%',
              width: '16px', height: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>3</span>
          </motion.div>
        )}

        {!compact && <ThemeToggle />}

        {!compact && !isSmall && (
          <LanguageSwitcher />
        )}

        <Link href="/profile" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: isSmall ? '4px' : '6px 12px',
          borderRadius: '10px',
          background: isSmall ? 'transparent' : colors.bg,
          border: isSmall ? 'none' : `1px solid ${colors.border}`,
          textDecoration: 'none',
          transition: 'border-color 0.2s ease',
        }}>
          <motion.div
            whileHover={{ scale: 1.05, boxShadow: `0 0 16px ${colors.primary}40` }}
            style={{
              width: '32px', height: '32px',
              borderRadius: '50%',
              background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 'bold',
              fontSize: '0.9rem',
              flexShrink: 0,
            }}
          >F</motion.div>
          {!isSmall && (
            <span style={{
              fontSize: '0.875rem',
              fontWeight: '500',
              color: colors.text,
            }}>Farmer</span>
          )}
        </Link>
      </div>
    </div>
  );
}