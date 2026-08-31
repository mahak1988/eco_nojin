import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Menu, X } from 'lucide-react';
import { AnimatedLogo } from '../branding/AnimatedLogo';
import { Button } from '../ui/Button';
import { toggleTheme, useThemeMode } from '../../hooks/useThemeMode';
import { useAuth } from '../../context/AuthContext';

const navItems = [
  { id: 'home', label: 'خانه', href: '/' },
  { id: 'features', label: 'ویژگی‌ها', href: '/features' },
  { id: 'pricing', label: 'قیمت‌گذاری', href: '/pricing' },
  { id: 'blog', label: 'وبلاگ', href: '/blog' },
  { id: 'about', label: 'درباره ما', href: '/about' },
];

export const PublicHeader: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const theme = useThemeMode();
  const { user } = useAuth();

  useEffect(() => {
    const h = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', h);
    return () => window.removeEventListener('scroll', h);
  }, []);

  return (
    <motion.header
      initial={{ y: -80 }}
      animate={{ y: 0 }}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 100,
        padding: '0.9rem 2rem',
        background: scrolled ? 'var(--color-surface)' : 'transparent',
        backdropFilter: scrolled ? 'blur(12px)' : 'none',
        borderBottom: scrolled ? '1px solid var(--color-border)' : 'none',
        transition: 'all .3s',
      }}
    >
      <div
        style={{
          maxWidth: 1400,
          margin: '0 auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
        }}
      >
        <AnimatedLogo size="sm" showSubtitle={false} />

        <nav style={{ display: 'flex', gap: '1.75rem' }} className="hidden md:flex">
          {navItems.map((n) => (
            <Link
              key={n.id}
              to={n.href}
              style={{
                color: 'var(--color-text-secondary)',
                textDecoration: 'none',
                fontSize: '0.95rem',
                fontWeight: 500,
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--color-primary)')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--color-text-secondary)')}
            >
              {n.label}
            </Link>
          ))}
        </nav>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Button variant="ghost" onClick={toggleTheme}>
            {theme === 'light' ? '🌙' : '☀️'}
          </Button>
          {user ? (
            <Link to="/hydroma">
              <Button variant="primary">داشبورد</Button>
            </Link>
          ) : (
            <>
              <Link to="/login" className="hidden md:block">
                <Button variant="secondary">ورود</Button>
              </Link>
              <Link to="/register" className="hidden md:block">
                <Button variant="primary">ثبت‌نام رایگان</Button>
              </Link>
            </>
          )}
          <button
            className="md:hidden btn btn-ghost"
            onClick={() => setOpen(!open)}
            style={{ padding: '0.5rem' }}
          >
            {open ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {open && (
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            background: 'var(--color-surface)',
            borderBottom: '1px solid var(--color-border)',
            padding: '1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}
        >
          {navItems.map((n) => (
            <Link
              key={n.id}
              to={n.href}
              onClick={() => setOpen(false)}
              style={{
                color: 'var(--color-text-primary)',
                textDecoration: 'none',
                padding: '0.7rem',
                borderRadius: 'var(--radius-lg)',
              }}
            >
              {n.label}
            </Link>
          ))}
          <Link to="/login" onClick={() => setOpen(false)}>
            <Button variant="secondary" style={{ width: '100%' }}>
              ورود
            </Button>
          </Link>
          <Link to="/register" onClick={() => setOpen(false)}>
            <Button variant="primary" style={{ width: '100%' }}>
              ثبت‌نام رایگان
            </Button>
          </Link>
        </motion.div>
      )}
    </motion.header>
  );
};
