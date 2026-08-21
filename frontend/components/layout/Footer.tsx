'use client';
import Link from 'next/link';
import { useI18n } from '../../lib/i18n-context';
import { useTheme } from '../../lib/theme-context';
import { useBreakpoint } from '../../lib/use-breakpoint';
import { motion } from 'framer-motion';
import { Leaf, Layers, BookOpen, ShieldCheck } from 'lucide-react';
import { FaFacebook, FaTwitter, FaLinkedin, FaInstagram, FaGithub, FaYoutube } from 'react-icons/fa';

export default function Footer() {
  const { t, direction } = useI18n();
  const { colors } = useTheme();
  const { isMobile } = useBreakpoint();

  const socials = [
    { id: 'fb', icon: FaFacebook, name: 'Facebook', color: '#1877f2' },
    { id: 'tw', icon: FaTwitter, name: 'Twitter', color: '#1da1f2' },
    { id: 'li', icon: FaLinkedin, name: 'LinkedIn', color: '#0077b5' },
    { id: 'ig', icon: FaInstagram, name: 'Instagram', color: '#e1306c' },
    { id: 'gh', icon: FaGithub, name: 'GitHub', color: '#333' },
    { id: 'yt', icon: FaYoutube, name: 'YouTube', color: '#ff0000' },
  ];

  const columns = [
    {
      id: 'platform',
      title: t('footer_platform'),
      icon: Layers,
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
      icon: BookOpen,
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
      icon: ShieldCheck,
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
      background: colors.bg === '#fffbeb' 
        ? 'linear-gradient(135deg, #064e3b 0%, #065f46 100%)'
        : 'linear-gradient(135deg, #064e3b 0%, #0a0f1c 100%)',
      color: 'white',
      padding: isMobile ? '40px 20px 24px' : '64px 48px 32px',
      marginTop: '80px',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Background orbs */}
      <motion.div
        animate={{ scale: [1, 1.15, 1], opacity: [0.4, 0.6, 0.4] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
        style={{
          position: 'absolute', top: '-50px', right: '-50px',
          width: '250px', height: '250px',
          background: `radial-gradient(circle, ${colors.primary}50 0%, transparent 70%)`,
          borderRadius: '50%',
          pointerEvents: 'none',
        }}
      />
      <motion.div
        animate={{ scale: [1, 1.1, 1], opacity: [0.3, 0.5, 0.3] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut", delay: 1 }}
        style={{
          position: 'absolute', bottom: '-80px', left: '-80px',
          width: '300px', height: '300px',
          background: `radial-gradient(circle, ${colors.accent}40 0%, transparent 70%)`,
          borderRadius: '50%',
          pointerEvents: 'none',
        }}
      />

      <div style={{
        display: 'grid',
        gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: isMobile ? '24px' : '32px',
        maxWidth: '1280px',
        margin: '0 auto',
        position: 'relative',
        zIndex: 1,
      }}>
        
        {/* Brand Section (First Card) */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          whileHover={{ y: -5, boxShadow: `0 10px 30px rgba(0,0,0,0.2)` }}
          style={{
            padding: '28px 24px',
            background: 'rgba(255,255,255,0.05)',
            backdropFilter: 'blur(8px)',
            borderRadius: '16px',
            border: '1px solid rgba(255,255,255,0.08)',
            transition: 'all 0.3s ease',
          }}
        >
          <div style={{
            display: 'flex', alignItems: 'center', gap: '12px',
            marginBottom: '16px',
          }}>
            <div style={{
              width: '48px', height: '48px', borderRadius: '14px',
              background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: `0 4px 16px ${colors.primary}60`,
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
            display: 'flex', gap: '10px', flexWrap: 'wrap',
          }}>
            {socials.map((s) => {
              const Icon = s.icon;
              return (
                <motion.a
                  key={s.id}
                  href="#"
                  whileHover={{ scale: 1.15, y: -3, backgroundColor: s.color }}
                  whileTap={{ scale: 0.9 }}
                  style={{
                    width: '42px', height: '42px', borderRadius: '12px',
                    background: 'rgba(255,255,255,0.1)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255,255,255,0.2)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: 'white', textDecoration: 'none',
                    transition: 'background-color 0.3s ease',
                  }}
                  title={s.name} aria-label={s.name}
                >
                  <Icon size={20} />
                </motion.a>
              );
            })}
          </div>
        </motion.div>

        {/* Link Columns as Beautiful Cards */}
        {columns.map((col, index) => {
          const Icon = col.icon;
          return (
            <motion.div
              key={col.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ y: -5, boxShadow: `0 10px 30px rgba(0,0,0,0.15)` }}
              style={{
                padding: '24px',
                background: 'rgba(255,255,255,0.05)',
                backdropFilter: 'blur(8px)',
                borderRadius: '16px',
                border: '1px solid rgba(255,255,255,0.08)',
                transition: 'all 0.3s ease',
              }}
            >
              <h4 style={{
                fontSize: '1rem', fontWeight: '700',
                marginBottom: '20px', color: '#d1fae5',
                display: 'flex', alignItems: 'center', gap: '8px',
              }}>
                <Icon size={18} color={colors.primary} />
                {col.title}
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {col.links.map(link => (
                  <Link key={link.id} href={link.href}>
                    <motion.div
                      whileHover={{ x: 6, color: colors.primary }}
                      style={{
                        fontSize: '0.9rem',
                        color: '#d1fae5',
                        opacity: 0.85,
                        cursor: 'pointer',
                        padding: '4px 0',
                        transition: 'color 0.2s',
                      }}
                    >
                      {link.label}
                    </motion.div>
                  </Link>
                ))}
              </div>
            </motion.div>
          );
        })}
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
          <span style={{ color: colors.primary }}>
            برنامه یکپارچه مهندسی منظر و احیای سرزمین
          </span>
        </div>
      </div>
    </footer>
  );
}