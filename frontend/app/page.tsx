'use client';
import Link from 'next/link';
import Footer from '../components/layout/Footer';
import { useI18n } from '../lib/i18n-context';
import { useTheme } from '../lib/theme-context';
import { useBreakpoint } from '../lib/use-breakpoint';
import { motion, useScroll, useTransform } from 'framer-motion';
import {
  Leaf, Satellite, Bot, TrendingUp, ShoppingCart,
  TreePine, Droplet, Mic, Wallet, Sparkles, Users,
  Globe2, ArrowRight, Heart,
  Shield, Zap, Award, TrendingDown
} from 'lucide-react';

const features = [
  { icon: Leaf, key: 'soil', color: '#f97316', gradient: 'linear-gradient(135deg, #f97316, #ea580c)' },
  { icon: Satellite, key: 'satellite', color: '#0ea5e9', gradient: 'linear-gradient(135deg, #0ea5e9, #0284c7)' },
  { icon: Bot, key: 'ai', color: '#8b5cf6', gradient: 'linear-gradient(135deg, #8b5cf6, #6d28d9)' },
  { icon: TrendingUp, key: 'scenarios', color: '#fbbf24', gradient: 'linear-gradient(135deg, #fbbf24, #d97706)' },
  { icon: ShoppingCart, key: 'marketplace', color: '#fb7185', gradient: 'linear-gradient(135deg, #fb7185, #e11d48)' },
  { icon: TreePine, key: 'carbon', color: '#0d9488', gradient: 'linear-gradient(135deg, #0d9488, #0f766e)' },
  { icon: Droplet, key: 'watershed', color: '#38bdf8', gradient: 'linear-gradient(135deg, #38bdf8, #0284c7)' },
  { icon: Mic, key: 'voice', color: '#fb7185', gradient: 'linear-gradient(135deg, #fb7185, #e11d48)' },
  { icon: Wallet, key: 'ecowallet', color: '#fbbf24', gradient: 'linear-gradient(135deg, #fbbf24, #f59e0b)' },
];

const stats = [
  { value: 40, suffix: '%', key: 'stat_degraded_land', icon: TrendingDown, color: '#f97316' },
  { value: 2, suffix: 'B+', key: 'stat_water_stress', icon: Droplet, color: '#0ea5e9' },
  { value: 41, suffix: '%', key: 'stat_drylands', icon: Globe2, color: '#fbbf24' },
  { value: 216, suffix: 'M', key: 'stat_climate_migrants', icon: Users, color: '#fb7185' },
];

function AnimatedCounter({ value, suffix }: Readonly<{ value: number; suffix: string }>) {
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    let frame = 0;
    const totalFrames = 45;
    const timer = window.setInterval(() => {
      frame += 1;
      setCurrent(Math.min(value, Math.round((value * frame) / totalFrames)));
      if (frame >= totalFrames) window.clearInterval(timer);
    }, 24);
    return () => window.clearInterval(timer);
  }, [value]);

  return <>{current}{suffix}</>;
}

import { useEffect, useState } from 'react';
import { CountryMapBackdrop } from '@/components/site/CountryMapBackdrop';

export default function HomePage() {
  const { t, direction } = useI18n();
  const { colors, theme } = useTheme();
  const { isMobile } = useBreakpoint();
  const { scrollY } = useScroll();
  const heroY = useTransform(scrollY, [0, 600], [0, 120]);
  const heroScale = useTransform(scrollY, [0, 600], [1, 0.92]);
  const heroOpacity = useTransform(scrollY, [0, 500], [1, 0.45]);
  const [typedText, setTypedText] = useState('برنامه یکپارچه مهندسی منظر');
  const [typedIndex, setTypedIndex] = useState(0);
  const typingLines = ['برنامه یکپارچه مهندسی منظر', 'احیای سرزمین با هوش مصنوعی', 'داده برای آب، خاک و زندگی'];

  useEffect(() => {
    const phrase = typingLines[typedIndex];
    let cursor = 0;
    setTypedText('');
    const timer = window.setInterval(() => {
      cursor += 1;
      setTypedText(phrase.slice(0, cursor));
      if (cursor >= phrase.length) {
        window.clearInterval(timer);
        window.setTimeout(() => setTypedIndex((value) => (value + 1) % typingLines.length), 1600);
      }
    }, 65);
    return () => window.clearInterval(timer);
  }, [typedIndex]);

  const container = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <div dir={direction} style={{ background: colors.bg, minHeight: '100vh' }}>
      {/* Hero Section */}
      <motion.section
        y={heroY}
        scale={heroScale}
        style={{
          position: 'relative',
          padding: isMobile ? '80px 20px 60px' : '120px 48px 100px',
          overflow: 'hidden',
          opacity: heroOpacity,
          background: theme === 'dark'
            ? 'radial-gradient(ellipse at top, rgba(249, 115, 22, 0.15), transparent 60%), #0c0a09'
            : 'radial-gradient(ellipse at top, rgba(249, 115, 22, 0.1), transparent 60%), #fffbeb',
        }}
      >
        <motion.div
          animate={{ y: [0, -20, 0], x: [0, 10, 0] }}
          transition={{ duration: 8, repeat: Infinity }}
          style={{
            position: 'absolute', top: '10%', left: '10%',
            width: '300px', height: '300px',
            background: 'radial-gradient(circle, rgba(249, 115, 22, 0.25), transparent 70%)',
            borderRadius: '50%', filter: 'blur(40px)', pointerEvents: 'none',
          }}
        />
        <motion.div
          animate={{ y: [0, 20, 0], x: [0, -10, 0] }}
          transition={{ duration: 10, repeat: Infinity }}
          style={{
            position: 'absolute', bottom: '10%', right: '10%',
            width: '400px', height: '400px',
            background: 'radial-gradient(circle, rgba(14, 165, 233, 0.2), transparent 70%)',
            borderRadius: '50%', filter: 'blur(40px)', pointerEvents: 'none',
          }}
        />

        <div style={{ maxWidth: '1100px', margin: '0 auto', textAlign: 'center', position: 'relative', zIndex: 1 }}>
          <CountryMapBackdrop />
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: '8px',
              padding: '8px 18px', background: colors.glass,
              backdropFilter: 'blur(20px)',
              border: `1px solid ${colors.border}`,
              borderRadius: '100px', fontSize: '0.875rem',
              fontWeight: '500', color: colors.primary,
              marginBottom: '24px',
            }}
          >
            <Sparkles size={14} />
            <span>{t('home_powered_by')}</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1 }}
            style={{
              fontSize: isMobile ? '2.25rem' : '4rem',
              fontWeight: '800', lineHeight: 1.1,
              marginBottom: '24px', letterSpacing: '-0.02em',
            }}
          >
            <span className="love-gradient-text">{t('home_hero_title')}</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            style={{
              fontSize: isMobile ? '1rem' : '1.25rem',
              color: colors.textMuted, maxWidth: '700px',
              margin: '0 auto 16px', lineHeight: 1.6,
            }}
          >
            {t('home_hero_subtitle')}
          </motion.p>

          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.25 }}
            style={{
              fontSize: isMobile ? '1.1rem' : '1.5rem',
              fontWeight: '700',
              marginBottom: '40px',
            }}
          >
            <span className="gradient-text">{typedText}<span className="typing-caret" aria-hidden="true">|</span></span>
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            style={{ display: 'flex', gap: '16px', justifyContent: 'center', flexWrap: 'wrap' }}
          >
            <Link href="/register">
              <motion.button
                whileHover={{ scale: 1.05, boxShadow: `0 20px 40px ${colors.primary}40` }}
                whileTap={{ scale: 0.98 }}
                style={{
                  padding: '16px 32px',
                  background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
                  color: 'white', border: 'none',
                  borderRadius: '12px', fontSize: '1rem',
                  fontWeight: '600', display: 'flex',
                  alignItems: 'center', gap: '8px',
                  cursor: 'pointer',
                  boxShadow: `0 8px 24px ${colors.primary}40`,
                }}
              >
                {t('home_cta_start')}
                <ArrowRight size={18} />
              </motion.button>
            </Link>
            <Link href="/mission">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.98 }}
                style={{
                  padding: '16px 32px',
                  background: colors.glass,
                  backdropFilter: 'blur(20px)',
                  color: colors.text,
                  border: `1.5px solid ${colors.border}`,
                  borderRadius: '12px', fontSize: '1rem',
                  fontWeight: '600', display: 'flex',
                  alignItems: 'center', gap: '8px',
                  cursor: 'pointer',
                }}
              >
                <Heart size={18} />
                {t('nav_mission')}
              </motion.button>
            </Link>
          </motion.div>

          {/* Global Stats */}
          <motion.div
            variants={container}
            initial="hidden"
            animate="show"
            style={{
              display: 'grid',
              gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(4, 1fr)',
              gap: '16px', marginTop: '80px',
              maxWidth: '900px', marginInline: 'auto',
            }}
          >
            {stats.map(stat => {
              const Icon = stat.icon;
              return (
                <motion.div
                  key={stat.key}
                  variants={item}
                  whileHover={{ y: -5, boxShadow: `0 16px 40px ${stat.color}20` }}
                  style={{
                    background: colors.glass,
                    backdropFilter: 'blur(20px)',
                    border: `1px solid ${colors.border}`,
                    padding: '20px 16px', borderRadius: '16px',
                    textAlign: 'center',
                  }}
                >
                  <Icon size={24} color={stat.color} style={{ marginBottom: '8px' }} />
                  <div style={{
                    fontSize: isMobile ? '1.75rem' : '2.25rem',
                    fontWeight: '800', color: stat.color, lineHeight: 1,
                  }}>
                    <AnimatedCounter value={stat.value} suffix={stat.suffix} />
                  </div>
                  <div style={{
                    fontSize: isMobile ? '0.75rem' : '0.85rem',
                    color: colors.textMuted, marginTop: '6px', lineHeight: 1.4,
                  }}>
                    {t(stat.key)}
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        </div>
      </motion.section>

      {/* Philosophy Section */}
      <section style={{
        padding: isMobile ? '60px 20px' : '100px 48px',
        background: theme === 'dark'
          ? 'linear-gradient(135deg, #1c1917 0%, #0c0a09 100%)'
          : 'linear-gradient(135deg, #fef3c7 0%, #fffbeb 100%)',
        position: 'relative',
        overflow: 'hidden',
      }}>
        <motion.div
          animate={{ scale: [1, 1.1, 1] }}
          transition={{ duration: 4, repeat: Infinity }}
          style={{
            position: 'absolute', top: '50%', left: '50%',
            transform: 'translate(-50%, -50%)',
            width: '600px', height: '600px',
            background: 'radial-gradient(circle, rgba(251, 113, 133, 0.1), transparent 70%)',
            borderRadius: '50%', filter: 'blur(60px)', pointerEvents: 'none',
          }}
        />
        <div style={{ maxWidth: '900px', margin: '0 auto', textAlign: 'center', position: 'relative', zIndex: 1 }}>
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <motion.div
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              style={{ fontSize: '3rem', marginBottom: '16px' }}
            >
              🌱
            </motion.div>
            <h2 style={{
              fontSize: isMobile ? '1.75rem' : '2.5rem',
              fontWeight: '800', marginBottom: '24px',
              letterSpacing: '-0.02em',
            }}>
              <span className="love-gradient-text">{t('home_philosophy_title')}</span>
            </h2>
            <p style={{
              fontSize: isMobile ? '1rem' : '1.15rem',
              color: colors.textMuted, lineHeight: 1.8,
              fontStyle: 'italic', marginBottom: '32px',
            }}>
              "{t('home_philosophy_text')}"
            </p>
            <div style={{
              display: 'flex', gap: '16px',
              justifyContent: 'center', flexWrap: 'wrap',
            }}>
              <Link href="/mission">
                <motion.button
                  whileHover={{ scale: 1.05, boxShadow: `0 12px 32px ${colors.primary}40` }}
                  whileTap={{ scale: 0.98 }}
                  style={{
                    padding: '12px 28px',
                    background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
                    color: 'white', border: 'none',
                    borderRadius: '10px', fontSize: '0.95rem',
                    fontWeight: '600', display: 'flex',
                    alignItems: 'center', gap: '8px',
                    cursor: 'pointer',
                  }}
                >
                  {t('nav_mission')}
                  <ArrowRight size={16} />
                </motion.button>
              </Link>
              <Link href="/donate">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.98 }}
                  style={{
                    padding: '12px 28px',
                    background: 'transparent',
                    color: colors.primary,
                    border: `2px solid ${colors.primary}`,
                    borderRadius: '10px', fontSize: '0.95rem',
                    fontWeight: '600', cursor: 'pointer',
                    display: 'flex', alignItems: 'center', gap: '8px',
                  }}
                >
                  <Heart size={16} />
                  {t('nav_donate')}
                </motion.button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section style={{ padding: isMobile ? '60px 20px' : '100px 48px', background: colors.bg }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto' }}>
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            style={{ textAlign: 'center', marginBottom: '64px' }}
          >
            <div style={{
              display: 'inline-block', padding: '6px 16px',
              background: `${colors.primary}15`,
              color: colors.primary, borderRadius: '100px',
              fontSize: '0.875rem', fontWeight: '600',
              marginBottom: '16px',
            }}>
              {t('home_features_badge')}
            </div>
            <h2 style={{
              fontSize: isMobile ? '1.75rem' : '2.5rem',
              fontWeight: '800', color: colors.text,
              marginBottom: '16px', letterSpacing: '-0.02em',
            }}>
              {t('home_features_title')}
            </h2>
            <p style={{
              fontSize: '1.15rem', color: colors.textMuted,
              maxWidth: '600px', margin: '0 auto',
            }}>
              {t('home_features_subtitle')}
            </p>
          </motion.div>

          <motion.div
            variants={container}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            style={{
              display: 'grid',
              gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fill, minmax(280px, 1fr))',
              gap: '24px',
            }}
          >
            {features.map((f) => {
              const Icon = f.icon;
              return (
                <Link key={f.key} href={`/modules/${f.key}`}>
                  <motion.div
                    variants={item}
                    whileHover={{ y: -8, rotateX: 3, rotateY: -3, scale: 1.02, boxShadow: `0 20px 40px ${f.color}25` }}
                    style={{
                      background: colors.cardBg,
                      backdropFilter: 'blur(20px)',
                      border: `1px solid ${colors.border}`,
                      padding: '32px', borderRadius: '20px',
                      height: '100%', position: 'relative',
                      overflow: 'hidden', cursor: 'pointer',
                      transition: 'all 0.3s',
                      transformPerspective: 900,
                    }}
                  >
                    <div style={{
                      position: 'absolute', top: '-30px', right: '-30px',
                      width: '120px', height: '120px',
                      background: `radial-gradient(circle, ${f.color}20, transparent 70%)`,
                      borderRadius: '50%',
                    }} />
                    <motion.div
                      whileHover={{ rotate: 360, scale: 1.1 }}
                      transition={{ duration: 0.6 }}
                      style={{
                        width: '64px', height: '64px',
                        borderRadius: '16px', background: f.gradient,
                        display: 'flex', alignItems: 'center',
                        justifyContent: 'center', marginBottom: '20px',
                        boxShadow: `0 8px 24px ${f.color}40`,
                        position: 'relative', zIndex: 1,
                      }}
                    >
                      <Icon size={30} color="white" strokeWidth={2.5} />
                    </motion.div>
                    <h3 style={{
                      fontSize: '1.25rem', fontWeight: '700',
                      color: colors.text, marginBottom: '10px',
                      position: 'relative', zIndex: 1,
                    }}>
                      {t(`module_${f.key}`)}
                    </h3>
                    <p style={{
                      color: colors.textMuted, fontSize: '0.95rem',
                      lineHeight: 1.6, marginBottom: '16px',
                      position: 'relative', zIndex: 1,
                    }}>
                      {t(`module_${f.key}_desc`)}
                    </p>
                    <div style={{
                      display: 'flex', alignItems: 'center', gap: '6px',
                      color: f.color, fontSize: '0.9rem',
                      fontWeight: '600', position: 'relative', zIndex: 1,
                    }}>
                      <span>Explore</span>
                      <ArrowRight size={16} />
                    </div>
                  </motion.div>
                </Link>
              );
            })}
          </motion.div>
        </div>
      </section>

      {/* Advantages Section */}
      <section style={{
        padding: isMobile ? '60px 20px' : '100px 48px',
        background: theme === 'dark'
          ? 'linear-gradient(180deg, #0c0a09 0%, #1c1917 100%)'
          : 'linear-gradient(180deg, #e0f2fe 0%, #fef3c7 100%)',
      }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            style={{ textAlign: 'center', marginBottom: '64px' }}
          >
            <div style={{
              display: 'inline-block', padding: '6px 16px',
              background: `${colors.accent}15`,
              color: colors.accent, borderRadius: '100px',
              fontSize: '0.875rem', fontWeight: '600',
              marginBottom: '16px',
            }}>
              {t('home_advantages_badge')}
            </div>
            <h2 style={{
              fontSize: isMobile ? '1.75rem' : '2.5rem',
              fontWeight: '800', color: colors.text,
              letterSpacing: '-0.02em',
            }}>
              {t('home_advantages_title')}
            </h2>
          </motion.div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '24px',
          }}>
            {[
              { icon: Globe2, title: t('advantage_channels_title'), desc: t('advantage_channels_desc'), color: '#0ea5e9' },
              { icon: Shield, title: t('advantage_rigor_title'), desc: t('advantage_rigor_desc'), color: '#f97316' },
              { icon: Zap, title: t('advantage_speed_title'), desc: t('advantage_speed_desc'), color: '#fbbf24' },
              { icon: Award, title: t('advantage_blockchain_title'), desc: t('advantage_blockchain_desc'), color: '#8b5cf6' },
            ].map((v, i) => {
              const Icon = v.icon;
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  whileHover={{ y: -8, rotateX: 3, rotateY: i % 2 ? 3 : -3 }}
                  style={{
                    background: colors.cardBg,
                    backdropFilter: 'blur(20px)',
                    border: `1px solid ${colors.border}`,
                    padding: '28px', borderRadius: '20px',
                    position: 'relative', overflow: 'hidden',
                    transformPerspective: 900,
                  }}
                >
                  <div style={{
                    position: 'absolute', top: '-30px', right: '-30px',
                    width: '100px', height: '100px',
                    background: `radial-gradient(circle, ${v.color}25, transparent 70%)`,
                    borderRadius: '50%',
                  }} />
                  <div style={{
                    width: '56px', height: '56px',
                    borderRadius: '14px', background: `${v.color}20`,
                    display: 'flex', alignItems: 'center',
                    justifyContent: 'center', marginBottom: '16px',
                    border: `2px solid ${v.color}30`,
                    position: 'relative', zIndex: 1,
                  }}>
                    <Icon size={28} color={v.color} strokeWidth={2.5} />
                  </div>
                  <h3 style={{
                    fontSize: '1.15rem', fontWeight: '700',
                    color: colors.text, marginBottom: '8px',
                    position: 'relative', zIndex: 1,
                  }}>
                    {v.title}
                  </h3>
                  <p style={{
                    color: colors.textMuted, fontSize: '0.9rem',
                    lineHeight: 1.6, position: 'relative', zIndex: 1,
                  }}>
                    {v.desc}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section style={{
        padding: isMobile ? '60px 20px' : '100px 48px',
        background: colors.bg,
      }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            style={{ textAlign: 'center', marginBottom: '64px' }}
          >
            <div style={{
              display: 'inline-block', padding: '6px 16px',
              background: `${colors.warm}25`,
              color: colors.primaryDark,
              borderRadius: '100px', fontSize: '0.875rem',
              fontWeight: '600', marginBottom: '16px',
            }}>
              {t('home_process_badge')}
            </div>
            <h2 style={{
              fontSize: isMobile ? '1.75rem' : '2.5rem',
              fontWeight: '800', color: colors.text,
              letterSpacing: '-0.02em',
            }}>
              {t('home_how_title')}
            </h2>
          </motion.div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(230px, 1fr))',
            gap: '32px',
          }}>
            {[
              { step: '01', icon: Users, title: t('home_step1_title'), desc: t('home_step1_desc') },
              { step: '02', icon: Satellite, title: t('home_step2_title'), desc: t('home_step2_desc') },
              { step: '03', icon: Leaf, title: t('home_step3_title'), desc: t('home_step3_desc') },
              { step: '04', icon: Wallet, title: t('home_step4_title'), desc: t('home_step4_desc') },
            ].map((s, i) => {
              const Icon = s.icon;
              return (
                <motion.div
                  key={s.step}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  whileHover={{ y: -8, rotateX: 3, rotateY: i % 2 ? 3 : -3 }}
                  style={{
                    background: colors.cardBg,
                    backdropFilter: 'blur(20px)',
                    border: `1px solid ${colors.border}`,
                    padding: '32px 24px', borderRadius: '20px',
                    textAlign: 'center', position: 'relative',
                    overflow: 'hidden',
                    transformPerspective: 900,
                    marginTop: !isMobile && i % 2 ? '24px' : undefined,
                  }}
                >
                  <div style={{
                    position: 'absolute', top: '12px', right: '12px',
                    fontSize: '3.5rem', fontWeight: '800',
                    color: `${colors.primaryLight}15`,
                    fontFamily: 'monospace',
                  }}>
                    {s.step}
                  </div>
                  <div style={{
                    width: '72px', height: '72px',
                    margin: '0 auto 20px', borderRadius: '20px',
                    background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
                    display: 'flex', alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: `0 8px 24px ${colors.primary}40`,
                    position: 'relative', zIndex: 1,
                  }}>
                    <Icon size={34} color="white" strokeWidth={2.5} />
                  </div>
                  <h3 style={{
                    fontSize: '1.2rem', fontWeight: '700',
                    color: colors.text, marginBottom: '10px',
                    position: 'relative', zIndex: 1,
                  }}>
                    {s.title}
                  </h3>
                  <p style={{
                    color: colors.textMuted, fontSize: '0.9rem',
                    lineHeight: 1.6, position: 'relative', zIndex: 1,
                  }}>
                    {s.desc}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{
        padding: isMobile ? '60px 20px' : '100px 48px',
        background: theme === 'dark'
          ? 'linear-gradient(135deg, #7c2d12 0%, #0c4a6e 100%)'
          : `linear-gradient(135deg, ${colors.primary} 0%, ${colors.accent} 100%)`,
        position: 'relative', overflow: 'hidden',
      }}>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 60, repeat: Infinity, ease: 'linear' }}
          style={{
            position: 'absolute', top: '-100px', right: '-100px',
            width: '400px', height: '400px',
            background: 'radial-gradient(circle, rgba(255,255,255,0.1), transparent 70%)',
            borderRadius: '50%', pointerEvents: 'none',
          }}
        />
        <div style={{
          maxWidth: '800px', margin: '0 auto',
          textAlign: 'center', position: 'relative',
          zIndex: 1, color: 'white',
        }}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
          >
            <Heart size={56} fill="white" color="white" style={{ marginBottom: '20px' }} />
            <h2 style={{
              fontSize: isMobile ? '1.75rem' : '3rem',
              fontWeight: '800', marginBottom: '20px',
              letterSpacing: '-0.02em',
            }}>
              {t('home_cta_title')}
            </h2>
            <p style={{
              fontSize: '1.2rem', opacity: 0.95,
              marginBottom: '40px',
            }}>
              {t('home_cta_subtitle')}
            </p>
            <div style={{
              display: 'flex', gap: '16px',
              justifyContent: 'center', flexWrap: 'wrap',
            }}>
              <Link href="/register">
                <motion.button
                  whileHover={{ scale: 1.05, boxShadow: '0 20px 50px rgba(0,0,0,0.3)' }}
                  whileTap={{ scale: 0.98 }}
                  style={{
                    padding: '18px 40px',
                    background: 'white',
                    color: colors.primary,
                    border: 'none', borderRadius: '14px',
                    fontSize: '1.1rem', fontWeight: '700',
                    display: 'inline-flex',
                    alignItems: 'center', gap: '10px',
                    cursor: 'pointer',
                  }}
                >
                  {t('home_cta_button')}
                  <ArrowRight size={20} />
                </motion.button>
              </Link>
              <Link href="/donate">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.98 }}
                  style={{
                    padding: '18px 40px',
                    background: 'transparent',
                    color: 'white',
                    border: '2px solid white',
                    borderRadius: '14px', fontSize: '1.1rem',
                    fontWeight: '700', display: 'inline-flex',
                    alignItems: 'center', gap: '10px',
                    cursor: 'pointer',
                  }}
                >
                  <Heart size={20} />
                  {t('nav_donate')}
                </motion.button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
