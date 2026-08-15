'use client';
import { useState } from 'react';
import Sidebar from '../../components/layout/Sidebar';
import TopBar from '../../components/layout/TopBar';
import { useTheme } from '../../lib/theme-context';
import { useBreakpoint } from '../../lib/use-breakpoint';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X } from 'lucide-react';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { colors } = useTheme();
  const { isMobile, isTablet } = useBreakpoint();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const isSmallScreen = isMobile || isTablet;

  return (
    <div style={{
      display: 'flex',
      minHeight: '100vh',
      background: colors.bg,
      position: 'relative',
    }}>
      {/* Desktop sidebar */}
      {!isSmallScreen && <Sidebar />}

      {/* Mobile sidebar overlay */}
      <AnimatePresence>
        {isSmallScreen && sidebarOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSidebarOpen(false)}
              style={{
                position: 'fixed',
                inset: 0,
                background: 'rgba(0,0,0,0.5)',
                backdropFilter: 'blur(4px)',
                zIndex: 1100,
              }}
            />
            <motion.div
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              style={{
                position: 'fixed',
                top: 0,
                left: 0,
                bottom: 0,
                zIndex: 1200,
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <Sidebar onClose={() => setSidebarOpen(false)} />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        minWidth: 0,
      }}>
        {/* Mobile hamburger + TopBar */}
        {isSmallScreen && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 12px',
            background: colors.cardBg,
            borderBottom: `1px solid ${colors.border}`,
          }}>
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={() => setSidebarOpen(true)}
              style={{
                width: '40px', height: '40px',
                borderRadius: '10px',
                border: `1px solid ${colors.border}`,
                background: colors.bg,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                cursor: 'pointer',
                flexShrink: 0,
              }}
            >
              <Menu size={20} color={colors.text} />
            </motion.button>
            <div style={{ flex: 1 }}><TopBar compact /></div>
          </div>
        )}

        {!isSmallScreen && <TopBar />}

        <main style={{
          flex: 1,
          padding: isMobile ? '16px' : isTablet ? '20px' : '24px',
          overflow: 'auto',
        }}>
          {children}
        </main>
      </div>
    </div>
  );
}
