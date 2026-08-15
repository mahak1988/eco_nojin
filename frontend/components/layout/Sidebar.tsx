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
  const { theme } = useTheme();

  const bg = theme === 'dark'
    ? 'linear-gradient(180deg, #064e3b 0%, #022c22 100%)'
    : 'linear-gradient(180deg, #064e3b 0%, #065f46 100%)';

  return (
    <aside style={{
      width: '260px',
      background: bg,
      color: 'white',
      padding: '20px 14px',
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      position: 'sticky',
      top: 0,
      overflowY: 'auto',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '8px 12px 24px',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        marginBottom: '20px',
      }}>
        <Link href="/" onClick={onClose} style={{
          display: 'flex', alignItems: 'center', gap: '10px',
        }}>
          <motion.div
            animate={{ rotate: [0, 5, -5, 0] }}
            transition={{ duration: 4, repeat: Infinity }}
            style={{
              width: '40px', height: '40px', borderRadius: '12px',
              background: 'linear-gradient(135deg, #10b981, #14b8a6)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 4px 16px rgba(16, 185, 129, 0.4)',
              flexShrink: 0,
            }}
          >
            <LogoLeaf size={22} color="white" strokeWidth={2.5} />
          </motion.div>
          <span style={{ fontSize: '1.25rem', fontWeight: '700' }}>Eco Nojin</span>
        </Link>
        {onClose && (
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={onClose}
            style={{
              width: '32px', height: '32px',
              borderRadius: '8px',
              background: 'rgba(255,255,255,0.1)',
              border: 'none',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer',
            }}
          >
            <X size={16} color="white" />
          </motion.button>
        )}
      </div>

      {/* Modules */}
      <div style={{
        fontSize: '0.75rem',
        textTransform: 'uppercase',
        letterSpacing: '1px',
        opacity: 0.6,
        padding: '0 12px 8px',
      }}>
        {t('nav_modules')}
      </div>

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
          return (
            <Link key={mod.key} href={mod.href} onClick={onClose}>
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.03 }}
                whileHover={{ x: 4 }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '11px 14px',
                  borderRadius: '10px',
                  background: isActive ? 'rgba(255,255,255,0.15)' : 'transparent',
                  color: isActive ? 'white' : '#a7f3d0',
                  fontSize: '0.9rem',
                  fontWeight: isActive ? '600' : '400',
                  position: 'relative',
                  transition: 'all 0.2s',
                }}
              >
                {isActive && (
                  <div style={{
                    position: 'absolute',
                    left: 0,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    width: '3px',
                    height: '24px',
                    background: 'linear-gradient(180deg, #10b981, #14b8a6)',
                    borderRadius: '0 3px 3px 0',
                  }} />
                )}
                <Icon size={18} style={{ flexShrink: 0 }} />
                <span>{t(`module_${mod.key}`)}</span>
              </motion.div>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div style={{
        borderTop: '1px solid rgba(255,255,255,0.1)',
        paddingTop: '16px',
        marginTop: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
      }}>
        <Link href="/profile" onClick={onClose}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '12px',
            padding: '10px 14px', borderRadius: '10px',
            color: '#a7f3d0', fontSize: '0.9rem',
          }}>
            <User size={18} />
            <span>{t('nav_profile')}</span>
          </div>
        </Link>
        <Link href="/settings" onClick={onClose}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '12px',
            padding: '10px 14px', borderRadius: '10px',
            color: '#a7f3d0', fontSize: '0.9rem',
          }}>
            <Settings size={18} />
            <span>{t('nav_settings')}</span>
          </div>
        </Link>
      </div>
    </aside>
  );
}
