'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useI18n } from '../../lib/i18n-context';
import { useTheme } from '../../lib/theme-context';
import { motion } from 'framer-motion';
import {
  LayoutDashboard, Leaf, Satellite, Bot, TrendingUp,
  ShoppingCart, TreePine, Droplet, Mic, Wallet,
  User, Settings, Leaf as LogoLeaf, X
} from 'lucide-react';

const modules = [
  { key: 'dashboard', icon: LayoutDashboard, href: '/dashboard' },
  { key: 'soil', icon: Leaf, href: '/modules/soil' },
  { key: 'satellite', icon: Satellite, href: '/modules/satellite' },
  { key: 'ai', icon: Bot, href: '/modules/ai' },
  { key: 'scenarios', icon: TrendingUp, href: '/modules/scenarios' },
  { key: 'marketplace', icon: ShoppingCart, href: '/modules/marketplace' },
  { key: 'carbon', icon: TreePine, href: '/modules/carbon' },
  { key: 'watershed', icon: Droplet, href: '/modules/watershed' },
  { key: 'voice', icon: Mic, href: '/modules/voice' },
  { key: 'ecowallet', icon: Wallet, href: '/modules/ecowallet' },
];

export default function Sidebar({ onClose }: { onClose?: () => void }) {
  const pathname = usePathname();
  const { t } = useI18n();
  const { theme, colors } = useTheme();

  // استایل پس‌زمینه بر اساس حالت تاریک/روشن
  const bgColor = theme === 'dark'
    ? 'linear-gradient(180deg, #064e3b 0%, #022c22 100%)'
    : 'linear-gradient(180deg, #ecfdf5 0%, #f0fdf4 100%)';

  return (
    <aside style={{
      width: '260px',
      background: bgColor,
      color: theme === 'dark' ? 'white' : colors.text,
      padding: '20px 14px',
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      position: 'sticky',
      top: 0,
      overflowY: 'auto',
      borderRight: `1px solid ${colors.border}`,
      // استایل اسکرول‌بار سفارشی
      scrollbarWidth: 'thin',
      scrollbarColor: `${colors.border} transparent`,
    }}>
      <style>{`
        /* استایل اسکرول‌بار برای مرورگرهای وب‌کیت */
        aside::-webkit-scrollbar {
          width: 6px;
        }
        aside::-webkit-scrollbar-track {
          background: transparent;
        }
        aside::-webkit-scrollbar-thumb {
          background-color: ${colors.border};
          border-radius: 10px;
        }
      `}</style>

      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '8px 12px 24px',
        borderBottom: `1px solid ${theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'}`,
        marginBottom: '20px',
      }}>
        <Link href="/" onClick={onClose} style={{
          display: 'flex', alignItems: 'center', gap: '10px',
          textDecoration: 'none',
        }}>
          <motion.div
            animate={{ rotate: [0, 5, -5, 0] }}
            transition={{ duration: 4, repeat: Infinity }}
            style={{
              width: '40px', height: '40px', borderRadius: '12px',
              background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: `0 4px 16px ${colors.primary}40`,
              flexShrink: 0,
            }}
          >
            <LogoLeaf size={22} color="white" strokeWidth={2.5} />
          </motion.div>
          <span style={{ fontSize: '1.25rem', fontWeight: '700', color: theme === 'dark' ? 'white' : colors.text }}>
            Eco Nojin
          </span>
        </Link>
        {onClose && (
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={onClose}
            style={{
              width: '32px', height: '32px',
              borderRadius: '8px',
              background: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)',
              border: 'none',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer',
              color: theme === 'dark' ? 'white' : colors.textMuted,
              transition: 'background 0.2s',
            }}
          >
            <X size={16} />
          </motion.button>
        )}
      </div>

      {/* Modules Title */}
      <div style={{
        fontSize: '0.75rem',
        textTransform: 'uppercase',
        letterSpacing: '1px',
        opacity: 0.5,
        padding: '0 12px 8px',
        color: theme === 'dark' ? 'white' : colors.textMuted,
      }}>
        {t('nav_modules')}
      </div>

      {/* Modules List */}
      <nav style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        gap: '2px',
        overflowY: 'auto',
      }}>
        {modules.map((mod, idx) => {
          const isActive = pathname === mod.href ||
                          (mod.href !== '/dashboard' && pathname.startsWith(mod.href));
          const Icon = mod.icon;
          const textColor = theme === 'dark' ? (isActive ? 'white' : '#a7f3d0') : (isActive ? colors.primary : colors.textMuted);

          return (
            <Link key={mod.key} href={mod.href} onClick={onClose} style={{ textDecoration: 'none' }}>
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.03 }}
                whileHover={{ 
                  x: 4,
                  background: theme === 'dark' ? 'rgba(255,255,255,0.08)' : `${colors.primary}15`,
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '11px 14px',
                  borderRadius: '10px',
                  background: isActive 
                    ? (theme === 'dark' ? 'rgba(255,255,255,0.12)' : `${colors.primary}20`)
                    : 'transparent',
                  color: textColor,
                  fontSize: '0.9rem',
                  fontWeight: isActive ? '600' : '400',
                  position: 'relative',
                  transition: 'all 0.2s ease',
                  cursor: 'pointer',
                }}
              >
                {/* نشانگر سمت چپ برای آیتم فعال */}
                {isActive && (
                  <motion.div
                    layoutId="sidebarActiveIndicator"
                    transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                    style={{
                      position: 'absolute',
                      left: 0,
                      top: '50%',
                      transform: 'translateY(-50%)',
                      width: '3px',
                      height: '24px',
                      background: `linear-gradient(180deg, ${colors.primary}, ${colors.accent})`,
                      borderRadius: '0 3px 3px 0',
                      boxShadow: `0 0 10px ${colors.primary}60`,
                    }}
                  />
                )}
                <Icon size={18} style={{ flexShrink: 0 }} />
                <span>{t(`module_${mod.key}`)}</span>
              </motion.div>
            </Link>
          );
        })}
      </nav>

      {/* Footer (Profile & Settings) */}
      <div style={{
        borderTop: `1px solid ${theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'}`,
        paddingTop: '16px',
        marginTop: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
      }}>
        <Link href="/profile" onClick={onClose} style={{ textDecoration: 'none' }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '12px',
            padding: '10px 14px', borderRadius: '10px',
            color: theme === 'dark' ? '#a7f3d0' : colors.textMuted,
            fontSize: '0.9rem',
            cursor: 'pointer',
            transition: 'background 0.2s ease',
          }}
          onMouseOver={(e) => (e.currentTarget.style.background = theme === 'dark' ? 'rgba(255,255,255,0.05)' : `${colors.primary}10`)}
          onMouseOut={(e) => (e.currentTarget.style.background = 'transparent')}
          >
            <User size={18} />
            <span>{t('nav_profile')}</span>
          </div>
        </Link>
        <Link href="/settings" onClick={onClose} style={{ textDecoration: 'none' }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '12px',
            padding: '10px 14px', borderRadius: '10px',
            color: theme === 'dark' ? '#a7f3d0' : colors.textMuted,
            fontSize: '0.9rem',
            cursor: 'pointer',
            transition: 'background 0.2s ease',
          }}
          onMouseOver={(e) => (e.currentTarget.style.background = theme === 'dark' ? 'rgba(255,255,255,0.05)' : `${colors.primary}10`)}
          onMouseOut={(e) => (e.currentTarget.style.background = 'transparent')}
          >
            <Settings size={18} />
            <span>{t('nav_settings')}</span>
          </div>
        </Link>
      </div>
    </aside>
  );
}