'use client';
import Link from 'next/link';
import { useI18n } from '../../lib/i18n-context';
import { useTheme } from '../../lib/theme-context';
import { useBreakpoint } from '../../lib/use-breakpoint';
import { motion } from 'framer-motion';
import { Leaf } from 'lucide-react';

export default function Footer() {
  const { t, direction } = useI18n();
  const { theme } = useTheme();
  const { isMobile } = useBreakpoint();

  const socials = [
    { id: 'fb', emoji: '📘', name: 'Facebook', color: '#1877f2' },
    { id: 'tw', emoji: '🐦', name: 'Twitter', color: '#1da1f2' },
    { id: 'li', emoji: '💼', name: 'LinkedIn', color: '#0077b5' },
    { id: 'ig', emoji: '📷', name: 'Instagram', color: '#e1306c' },
    { id: 'gh', emoji: '💻', name: 'GitHub', color: '#333' },
    { id: 'yt', emoji: '▶️', name: 'YouTube', color: '#ff0000' },
  ];

  // UNIQUE IDs for all links - FIXES the duplicate key error!
  const columns = [
    {
      id: 'platform',
      title: t('footer_platform'),
      links: [
        { id: 'p-modules', label: t('nav_modules'), href: '/dashboard' },
        { id: 'p-pricing', label: t('nav_pricing'), href: '/pricing' },
        { id: 'p-about', label: t('nav_about'), href: '/about' },
        { id: 'p-contact', label: t('nav_contact'), href: '/contact' },
      ]
    },
    {
      id: 'resources',
      title: t('footer_resources'),
      links: [
        { id: 'r-docs', label: t('footer_docs'), href: '/docs' },
        { id: 'r-api', label: t('footer_api'), href: '/docs/api' },
        { id: 'r-blog', label: t('footer_blog'), href: '/blog' },
        { id: 'r-support', label: t('footer_support'), href: '/support' },
        { id: 'r-mission', label: t('nav_mission'), href: '/mission' },
        { id: 'r-donate', label: t('nav_donate'), href: '/donate' },
      ]
    },
    {
      id: 'legal',
      title: t('footer_legal'),
      links: [
        { id: 'l-privacy', label: t('footer_privacy'), href: '/legal/privacy' },
        { id: 'l-terms', label: t('footer_terms'), href: '/legal/terms' },
        { id: 'l-cookies', label: t('footer_cookies'), href: '/legal/cookies' },
        { id: 'l-security', label: t('footer_security'), href: '/legal/security' },
      ]
    },
  ];

  return (
    <footer dir={direction} style={{
      background: theme === 'dark'
        ? 'linear-gradient(135deg, #064e3b 0%, #0a0f1c 100%)'
        : 'linear-gradient(135deg, #064e3b 0%, #065f46 100%)',
      color: 'white',
      padding: isMobile ? '40px 20px 24px' : '64px 48px 32px',
      marginTop: '80px',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Background orbs */}
      <div style={{
        position: 'absolute', top: '-50px', right: '-50px',
        width: '200px', height: '200px',
        background: 'radial-gradient(circle, rgba(16, 185, 129, 0.3) 0%, transparent 70%)',
        borderRadius: '50%',
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute', bottom: '-80px', left: '-80px',
        width: '300px', height: '300px',
        background: 'radial-gradient(circle, rgba(20, 184, 166, 0.2) 0%, transparent 70%)',
        borderRadius: '50%',
        pointerEvents: 'none',
      }} />

      <div style={{
        display: 'grid',
        gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: isMobile ? '32px' : '40px',
        maxWidth: '1280px',
        margin: '0 auto',
        position: 'relative',
        zIndex: 1,
      }}>
        {/* Brand */}
        <div>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '12px',
            marginBottom: '16px',
          }}>
            <div style={{
              width: '48px', height: '48px', borderRadius: '14px',
              background: 'linear-gradient(135deg, #10b981, #14b8a6)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 4px 16px rgba(16, 185, 129, 0.4)',
              flexShrink: 0,
            }}>
              <Leaf size={24} color="white" strokeWidth={2.5} />
            </div>
            <span style={{ fontSize: '1.75rem', fontWeight: '700' }}>Eco Nojin</span>
          </div>
          <p style={{
            fontSize: '0.95rem', opacity: 0.9,
            maxWidth: '400px', lineHeight: 1.7,
            marginBottom: '24px',
          }}>
            {t('footer_main_tagline')}
          </p>
          <div style={{
            display: 'flex',
            gap: '10px',
            flexWrap: 'wrap',
          }}>
            {socials.map((s) => (
              <motion.a
                key={s.id}
                href="#"
                whileHover={{ scale: 1.15, y: -3 }}
                whileTap={{ scale: 0.9 }}
                style={{
                  width: '42px', height: '42px',
                  borderRadius: '12px',
                  background: 'rgba(255,255,255,0.1)',
                  backdropFilter: 'blur(10px)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.2rem',
                  textDecoration: 'none',
                }}
                title={s.name}
                aria-label={s.name}
              >
                {s.emoji}
              </motion.a>
            ))}
          </div>
        </div>

        {/* Link columns */}
        {columns.map(col => (
          <div key={col.id}>
            <h4 style={{
              fontSize: '1rem', fontWeight: '700',
              marginBottom: '20px', color: '#d1fae5',
              position: 'relative', paddingBottom: '8px',
            }}>
              {col.title}
              <div style={{
                position: 'absolute', bottom: 0, left: 0,
                width: '30px', height: '2px',
                background: 'linear-gradient(90deg, #10b981, transparent)',
              }} />
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {col.links.map(link => (
                <Link key={link.id} href={link.href}>
                  <motion.div
                    whileHover={{ x: 5 }}
                    style={{
                      fontSize: '0.9rem',
                      color: '#d1fae5',
                      opacity: 0.85,
                      transition: 'all 0.2s',
                      cursor: 'pointer',
                    }}
                  >
                    {link.label}
                  </motion.div>
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div style={{
        borderTop: '1px solid rgba(255,255,255,0.15)',
        marginTop: isMobile ? '32px' : '48px',
        paddingTop: '24px',
        textAlign: 'center',
        fontSize: '0.875rem',
        opacity: 0.8,
        maxWidth: '1280px',
        marginInline: 'auto',
        position: 'relative',
        zIndex: 1,
      }}>
        © 2026 Eco Nojin. {t('footer_rights')}
        <div style={{ marginTop: '8px' }}>
          <span style={{ color: '#f97316' }}>{t('home_hero_sub2')}</span>
        </div>
      </div>
    </footer>
  );
}
