#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Eco Nojin - تجربه کلاس جهانی: خانه زنده + Auth + Pricing + HyDroMa Dashboard"""

import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path("D:/eco_nojin")
FE = ROOT / "frontend"
BAK = ROOT / f"_backup_phase5_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def log(m, i="+"): print(f"  [{i}] {m}")
def wf(p: Path, c: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(c, encoding="utf-8")

def backup():
    BAK.mkdir(parents=True, exist_ok=True)
    for d in ["src/pages", "src/components", "src/styles", "src/App.tsx"]:
        s = FE / d
        if s.exists():
            dst = BAK / d
            if s.is_dir():
                if dst.exists(): shutil.rmtree(dst)
                shutil.copytree(s, dst)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(s, dst)
    log(f"Backup: {BAK.name}")

# ═══════════════ 1) useThemeMode hook ═══════════════
def build_hook():
    wf(FE / "src/hooks/useThemeMode.ts", r'''import { useEffect, useState } from 'react';

export type ThemeMode = 'light' | 'dark';

export function useThemeMode(): ThemeMode {
  const [mode, setMode] = useState<ThemeMode>(() =>
    (localStorage.getItem('theme') as ThemeMode) || 'light'
  );
  useEffect(() => {
    const h = (e: Event) => {
      const d = (e as CustomEvent).detail as ThemeMode;
      if (d) setMode(d);
    };
    window.addEventListener('eco-theme-change', h);
    return () => window.removeEventListener('eco-theme-change', h);
  }, []);
  return mode;
}

export function toggleTheme() {
  const cur = (localStorage.getItem('theme') as ThemeMode) || 'light';
  const next: ThemeMode = cur === 'light' ? 'dark' : 'light';
  localStorage.setItem('theme', next);
  document.documentElement.setAttribute('data-theme', next);
  window.dispatchEvent(new CustomEvent('eco-theme-change', { detail: next }));
}
''')
    log("useThemeMode.ts")

# ═══════════════ 2) LivingBackground ═══════════════
def build_background():
    wf(FE / "src/components/backgrounds/LivingBackground.tsx", r'''import React, { useMemo } from 'react';
import { useThemeMode } from '../../hooks/useThemeMode';

interface Props { showRain?: boolean; showBirds?: boolean; showWater?: boolean; }

/** پس‌زمینه زنده: آسمان + خورشید/ماه + ابر + باران + پرنده + آب */
export const LivingBackground: React.FC<Props> = ({
  showRain = true, showBirds = true, showWater = true,
}) => {
  const dark = useThemeMode() === 'dark';

  const drops = useMemo(() =>
    Array.from({ length: 34 }, (_, i) => ({
      left: (i * 97) % 100, delay: (i * 0.37) % 4, dur: 2.6 + ((i * 13) % 20) / 10,
    })), []);
  const birds = useMemo(() =>
    Array.from({ length: 3 }, (_, i) => ({
      top: 10 + i * 8, dur: 26 + i * 9, delay: i * 7, scale: 0.7 + i * 0.25,
    })), []);
  const stars = useMemo(() =>
    Array.from({ length: 40 }, (_, i) => ({
      left: (i * 61) % 100, top: (i * 37) % 55, s: 1 + (i % 3), d: (i * 0.53) % 3,
    })), []);

  return (
    <div aria-hidden style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none', zIndex: 0 }}>
      <div className={dark ? 'sky-dark' : 'sky-light'} style={{ position: 'absolute', inset: 0 }} />

      {dark && stars.map((st, i) => (
        <span key={i} className="star" style={{ left: st.left + '%', top: st.top + '%', width: st.s, height: st.s, animationDelay: st.d + 's' }} />
      ))}

      <div className={dark ? 'moon' : 'sun'} />

      {/* تپه‌های خاکی */}
      <svg className="hill" viewBox="0 0 1440 220" preserveAspectRatio="none" style={{ height: 180 }}>
        <path d="M0,160 C240,60 480,200 720,120 C960,40 1200,180 1440,100 L1440,220 L0,220 Z"
          fill={dark ? '#2a2119' : '#d9ead3'} />
        <path d="M0,190 C300,110 600,220 900,150 C1150,95 1300,200 1440,150 L1440,220 L0,220 Z"
          fill={dark ? '#1e1a16' : '#c4ddb8'} opacity="0.9" />
      </svg>

      <div className="cloud" style={{ top: '10%', animationDuration: '80s' }} />
      <div className="cloud" style={{ top: '22%', animationDuration: '110s', animationDelay: '-30s', transform: 'scale(0.7)' }} />
      <div className="cloud" style={{ top: '5%', animationDuration: '95s', animationDelay: '-60s', transform: 'scale(0.85)' }} />

      {showRain && drops.map((d, i) => (
        <span key={i} className="raindrop" style={{ left: d.left + '%', animationDelay: d.delay + 's', animationDuration: d.dur + 's' }} />
      ))}

      {showBirds && birds.map((b, i) => (
        <svg key={i} className="bird" viewBox="0 0 100 40"
          style={{ top: b.top + '%', animationDuration: b.dur + 's', animationDelay: b.delay + 's', transform: `scale(${b.scale})` }}>
          <path d="M5,25 Q25,5 50,22 Q75,5 95,25" fill="none" stroke="currentColor" strokeWidth="5" strokeLinecap="round" />
        </svg>
      ))}

      {showWater && (
        <div className="water">
          <svg className="wave" viewBox="0 0 2880 120" preserveAspectRatio="none">
            <path d="M0,60 C240,100 480,20 720,60 C960,100 1200,20 1440,60 C1680,100 1920,20 2160,60 C2400,100 2640,20 2880,60 L2880,120 L0,120 Z"
              fill={dark ? 'rgba(30,58,90,0.8)' : 'rgba(59,130,246,0.35)'} />
          </svg>
          <svg className="wave w2" viewBox="0 0 2880 120" preserveAspectRatio="none">
            <path d="M0,70 C240,30 480,110 720,70 C960,30 1200,110 1440,70 C1680,30 1920,110 2160,70 C2400,30 2640,110 2880,70 L2880,120 L0,120 Z"
              fill={dark ? 'rgba(20,40,70,0.9)' : 'rgba(37,99,235,0.45)'} />
          </svg>
        </div>
      )}
    </div>
  );
};
''')
    log("LivingBackground.tsx")

# ═══════════════ 3) AnimatedLogo ═══════════════
def build_logo():
    wf(FE / "src/components/branding/AnimatedLogo.tsx", r'''import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Leaf, Droplets } from 'lucide-react';

interface Props { size?: 'sm' | 'md' | 'lg'; showSubtitle?: boolean; }

/** لوگو: Eco Nojin -> خانه | HyDroMa -> داشبورد */
export const AnimatedLogo: React.FC<Props> = ({ size = 'md', showSubtitle = true }) => {
  const fs = size === 'lg' ? '2.5rem' : size === 'md' ? '1.5rem' : '1.2rem';
  const is = size === 'lg' ? 34 : size === 'md' ? 22 : 18;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', direction: 'ltr' }}>
        <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 8 }} title="صفحه خانه">
          <motion.span whileHover={{ scale: 1.15, rotate: -8 }} style={{ display: 'inline-flex', color: '#22c55e' }}>
            <Leaf size={is} className="animate-float" />
          </motion.span>
          <motion.span whileHover={{ scale: 1.06 }} className="logo-eco-nojin" style={{ fontSize: fs }}>
            Eco Nojin
          </motion.span>
        </Link>

        <span style={{ color: 'var(--color-text-tertiary)', fontWeight: 300 }}>×</span>

        <Link to="/hydroma" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 8 }} title="داشبورد HyDroMa">
          <motion.span whileHover={{ scale: 1.15, y: 3 }} style={{ display: 'inline-flex', color: '#3b82f6' }}>
            <Droplets size={is} className="animate-float-slow" />
          </motion.span>
          <motion.span whileHover={{ scale: 1.06 }} className="logo-hydroma" style={{ fontSize: fs }}>
            HyDroMa
          </motion.span>
        </Link>
      </div>
      {showSubtitle && (
        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-tertiary)', margin: 0 }}>
          پلتفرم یکپارچه کشاورزی پایدار و مدیریت هوشمند آب
        </p>
      )}
    </div>
  );
};
''')
    log("AnimatedLogo.tsx")

# ═══════════════ 4) AuthContext + ProtectedRoute ═══════════════
def build_auth():
    wf(FE / "src/context/AuthContext.tsx", r'''import React, { createContext, useContext, useEffect, useState } from 'react';

export interface AuthUser {
  name: string; email: string; role: string; plan: string;
}

interface AuthCtx {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<AuthUser>;
  register: (data: { name: string; email: string; role: string }) => Promise<AuthUser>;
  logout: () => void;
}

const Ctx = createContext<AuthCtx | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const raw = localStorage.getItem('eco_user');
    if (raw) { try { setUser(JSON.parse(raw)); } catch { /* ignore */ } }
    setLoading(false);
  }, []);

  const persist = (u: AuthUser) => { setUser(u); localStorage.setItem('eco_user', JSON.stringify(u)); };

  const login: AuthCtx['login'] = async (email, password) => {
    await new Promise(r => setTimeout(r, 900));
    if (!email.includes('@') || password.length < 6) throw new Error('ایمیل یا رمز عبور معتبر نیست');
    const u: AuthUser = { name: email.split('@')[0], email, role: 'farmer', plan: 'free' };
    persist(u); return u;
  };

  const register: AuthCtx['register'] = async (data) => {
    await new Promise(r => setTimeout(r, 1100));
    const u: AuthUser = { name: data.name, email: data.email, role: data.role, plan: 'free' };
    persist(u); return u;
  };

  const logout = () => { setUser(null); localStorage.removeItem('eco_user'); };

  return <Ctx.Provider value={{ user, loading, login, register, logout }}>{children}</Ctx.Provider>;
};

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
''')

    wf(FE / "src/components/auth/ProtectedRoute.tsx", r'''import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Loader2 } from 'lucide-react';

export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Loader2 size={40} className="animate-spin" style={{ color: 'var(--color-primary)' }} />
      </div>
    );
  }
  if (!user) return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  return <>{children}</>;
};
''')
    log("AuthContext + ProtectedRoute")

# ═══════════════ 5) ModuleCard ═══════════════
def build_module_card():
    wf(FE / "src/components/ui/ModuleCard.tsx", r'''import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Lock, ArrowLeft } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface Props {
  title: string; description: string; icon: React.ReactNode;
  color: string; to: string; badge?: string;
}

export const ModuleCard: React.FC<Props> = ({ title, description, icon, color, to, badge }) => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const go = () => user ? navigate(to) : navigate('/login', { state: { from: to } });

  return (
    <motion.div
      onClick={go}
      whileHover={{ y: -10, scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className="card"
      style={{ cursor: 'pointer', borderTop: `4px solid ${color}`, position: 'relative', overflow: 'hidden', padding: '1.75rem' }}
    >
      <div style={{ position: 'absolute', inset: 0, background: `radial-gradient(500px circle at 0% 0%, ${color}18, transparent 60%)`, pointerEvents: 'none' }} />
      {badge && <span className="badge" style={{ position: 'absolute', top: 12, left: 12, background: color + '22', color }}>{badge}</span>}

      <motion.div
        whileHover={{ rotate: 6, scale: 1.1 }}
        style={{ width: 60, height: 60, borderRadius: 'var(--radius-xl)', background: color, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', marginBottom: '1.25rem', boxShadow: `0 8px 20px ${color}55` }}
      >
        {icon}
      </motion.div>

      <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem' }}>{title}</h3>
      <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem', lineHeight: 1.7, marginBottom: '1rem' }}>{description}</p>

      <div style={{ display: 'flex', alignItems: 'center', gap: 6, color, fontSize: '0.875rem', fontWeight: 600 }}>
        {!user && <Lock size={14} />}
        <span>{user ? 'باز کردن ماژول' : 'ورود برای دسترسی'}</span>
        <ArrowLeft size={14} className="animate-pulse" />
      </div>
    </motion.div>
  );
};
''')
    log("ModuleCard.tsx")

# ═══════════════ 6) HomePage ═══════════════
def build_home():
    wf(FE / "src/pages/HomePage.tsx", r'''import React from 'react';
import { motion } from 'framer-motion';
import {
  Sprout, Droplets, Wind, Beef, Leaf, Map, Store, Compass,
  BarChart3, Satellite, TrendingUp, Users, Globe, Zap,
} from 'lucide-react';
import { PublicLayout } from '../components/layout/PublicLayout';
import { LivingBackground } from '../components/backgrounds/LivingBackground';
import { AnimatedLogo } from '../components/branding/AnimatedLogo';
import { ModuleCard } from '../components/ui/ModuleCard';
import { Button } from '../components/ui/Button';

const modules = [
  { title: 'برنامه کشت', description: 'شبیه‌سازی رشد محصول و مقایسه سناریوهای کشت چندلایه', icon: <Sprout size={28} />, color: '#22c55e', to: '/simulator' },
  { title: 'مدیریت آب', description: 'بودجه آب، نفوذپذیری، رواناب و تغذیه آبخوان', icon: <Droplets size={28} />, color: '#3b82f6', to: '/simulator' },
  { title: 'باد و فرسایش', description: 'تحلیل فرسایش بادی/آبی و طراحی بادشکن', icon: <Wind size={28} />, color: '#f59e0b', to: '/simulator' },
  { title: 'دامداری', description: 'شبیه‌ساز گاو، گوسفند، بز و طیور + اقتصاد گله', icon: <Beef size={28} />, color: '#b45309', to: '/simulator' },
  { title: 'کربن و اعتبار', description: 'پیش‌بینی ترشح کربن و صدور اعتبار کربن', icon: <Leaf size={28} />, color: '#10b981', to: '/simulator' },
  { title: 'نقشه و زمین', description: 'نمای سه‌بعدی مزرعه و تحلیل زمین', icon: <Map size={28} />, color: '#8b5cf6', to: '/simulator' },
  { title: 'بازارچه محلی', description: 'فروش مستقیم محصول بدون واسطه', icon: <Store size={28} />, color: '#eab308', to: '/simulator' },
  { title: 'گردشگری بوم‌گردی', description: 'تورهای روستایی و درآمد پایدار', icon: <Compass size={28} />, color: '#06b6d4', to: '/simulator' },
  { title: 'گزارش‌ها', description: 'تحلیل سودآوری و گزارش پایداری', icon: <BarChart3 size={28} />, color: '#6366f1', to: '/simulator' },
  { title: 'پایش ماهواره‌ای', description: 'NDVI و سلامت گیاه از فضا', icon: <Satellite size={28} />, color: '#0ea5e9', to: '/simulator' },
];

const stats = [
  { value: '۵۰۰+', label: 'مزرعه فعال', icon: Users },
  { value: '۴۰٪', label: 'کاهش مصرف آب', icon: Droplets },
  { value: '۴۵٪', label: 'افزایش عملکرد', icon: TrendingUp },
  { value: '۱۲', label: 'کشور', icon: Globe },
];

export const HomePage: React.FC = () => {
  return (
    <PublicLayout>
      {/* HERO زنده */}
      <section style={{ position: 'relative', minHeight: '92vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '6rem 2rem 8rem', overflow: 'hidden' }}>
        <LivingBackground />
        <div style={{ position: 'relative', zIndex: 1, textAlign: 'center', maxWidth: 1000 }}>
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}>
            <AnimatedLogo size="lg" />
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2, duration: 0.7 }}
            style={{ fontSize: 'clamp(2.2rem, 5.5vw, 3.8rem)', fontWeight: 800, margin: '2.5rem 0 1.25rem', lineHeight: 1.25 }}
          >
            آینده کشاورزی،
            <span className="gradient-text"> پایدار و هوشمند</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35, duration: 0.7 }}
            style={{ fontSize: '1.2rem', color: 'var(--color-text-secondary)', maxWidth: 720, margin: '0 auto 2.5rem', lineHeight: 1.9 }}
          >
            از قطره تا اقیانوس، از دانه تا جنگل.
            <br />
            با شبیه‌سازهای علمی و داده ماهواره‌ای، مزرعه‌ات را مانند یک اکوسیستم زنده مدیریت کن.
          </motion.p>

          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5, duration: 0.7 }}
            style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button variant="primary" size="lg" icon={<Zap size={18} className="animate-pulse" />}>شروع رایگان</Button>
            <Button variant="secondary" size="lg">مشاهده دمو</Button>
          </motion.div>
        </div>
      </section>

      {/* Stats */}
      <section style={{ padding: '4rem 2rem', background: 'var(--color-surface)' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '2rem' }}>
          {stats.map((s, i) => {
            const Icon = s.icon;
            return (
              <motion.div key={i} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }} style={{ textAlign: 'center' }}>
                <motion.div whileHover={{ scale: 1.15, rotate: 8 }} style={{ display: 'inline-flex', color: 'var(--color-primary)', marginBottom: '0.75rem' }}>
                  <Icon size={34} className="animate-float" />
                </motion.div>
                <div style={{ fontSize: '2.4rem', fontWeight: 800 }}>{s.value}</div>
                <div style={{ color: 'var(--color-text-secondary)' }}>{s.label}</div>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* Module cards */}
      <section style={{ padding: '6rem 2rem' }}>
        <div style={{ maxWidth: 1400, margin: '0 auto' }}>
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
            <h2 style={{ fontSize: '2.5rem', fontWeight: 800, marginBottom: '1rem' }}>ماژول‌های پلتفرم</h2>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '1.1rem' }}>
              برای باز کردن هر ماژول، ابتدا وارد حساب کاربری شوید
            </p>
          </motion.div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.75rem' }}>
            {modules.map((m, i) => (
              <motion.div key={m.title} initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: (i % 4) * 0.08 }}>
                <ModuleCard {...m} />
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </PublicLayout>
  );
};
''')
    log("HomePage.tsx (زنده)")

# ═══════════════ 7) Auth pages ═══════════════
def build_auth_pages():
    base = FE / "src/pages/auth"

    wf(base / "AuthShell.tsx", r'''import React from 'react';
import { motion } from 'framer-motion';
import { LivingBackground } from '../../components/backgrounds/LivingBackground';
import { AnimatedLogo } from '../../components/branding/AnimatedLogo';

export const AuthShell: React.FC<{ children: React.ReactNode; title: string; subtitle: string }> = ({ children, title, subtitle }) => (
  <div style={{ minHeight: '100vh', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '4rem 1.5rem', overflow: 'hidden' }}>
    <LivingBackground showRain />
    <motion.div
      initial={{ opacity: 0, y: 40, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.6, type: 'spring', damping: 18 }}
      className="glass"
      style={{ position: 'relative', zIndex: 1, width: '100%', maxWidth: 460, borderRadius: 'var(--radius-2xl)', padding: '2.5rem', boxShadow: 'var(--shadow-2xl)' }}
    >
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <AnimatedLogo size="sm" showSubtitle={false} />
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, marginTop: '1.25rem', marginBottom: '0.5rem' }}>{title}</h1>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>{subtitle}</p>
      </div>
      {children}
    </motion.div>
  </div>
);

export const Field: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
  <motion.label initial={{ opacity: 0, x: -14 }} animate={{ opacity: 1, x: 0 }} style={{ display: 'block', marginBottom: '1.1rem' }}>
    <span style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 6, color: 'var(--color-text-secondary)' }}>{label}</span>
    {children}
  </motion.label>
);
''')

    wf(base / "LoginPage.tsx", r'''import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Mail, Lock, Eye, EyeOff, Loader2, Wallet, Chrome } from 'lucide-react';
import { AuthShell, Field } from './AuthShell';
import { Button } from '../../components/ui/Button';
import { useAuth } from '../../context/AuthContext';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as any)?.from || '/hydroma';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(''); setBusy(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.message);
    } finally { setBusy(false); }
  };

  return (
    <AuthShell title="خوش آمدید" subtitle="برای دسترسی به ماژول‌ها وارد شوید">
      <form onSubmit={submit}>
        {error && <div className="badge badge-error" style={{ width: '100%', justifyContent: 'center', marginBottom: '1rem', padding: '0.6rem' }}>{error}</div>}

        <Field label="ایمیل">
          <div style={{ position: 'relative' }}>
            <Mail size={16} style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-tertiary)' }} />
            <input className="input" dir="ltr" style={{ paddingRight: '2.4rem', textAlign: 'left' }} type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="you@farm.ir" />
          </div>
        </Field>

        <Field label="رمز عبور">
          <div style={{ position: 'relative' }}>
            <Lock size={16} style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-tertiary)' }} />
            <input className="input" dir="ltr" style={{ paddingRight: '2.4rem', paddingLeft: '2.4rem', textAlign: 'left' }} type={showPass ? 'text' : 'password'} required minLength={6} value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" />
            <button type="button" onClick={() => setShowPass(!showPass)} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-tertiary)' }}>
              {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </Field>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.4rem', fontSize: '0.85rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--color-text-secondary)', cursor: 'pointer' }}>
            <input type="checkbox" checked={remember} onChange={e => setRemember(e.target.checked)} />
            مرا به خاطر بسپار
          </label>
          <Link to="/forgot-password" style={{ color: 'var(--color-primary)', fontWeight: 600 }}>فراموشی رمز؟</Link>
        </div>

        <Button variant="primary" size="lg" loading={busy} style={{ width: '100%' }}>
          {!busy && <Lock size={16} />} ورود به حساب
        </Button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', margin: '1.4rem 0', color: 'var(--color-text-tertiary)', fontSize: '0.8rem' }}>
          <div style={{ flex: 1, height: 1, background: 'var(--color-border)' }} /> یا <div style={{ flex: 1, height: 1, background: 'var(--color-border)' }} />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
          <Button variant="secondary" icon={<Chrome size={16} />}>Google</Button>
          <Button variant="secondary" icon={<Wallet size={16} />}>Wallet</Button>
        </div>

        <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
          حساب ندارید؟ <Link to="/register" style={{ color: 'var(--color-primary)', fontWeight: 700 }}>ثبت‌نام رایگان</Link>
        </p>
      </form>
    </AuthShell>
  );
};
''')

    wf(base / "RegisterPage.tsx", r'''import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, Mail, Phone, Lock, Loader2 } from 'lucide-react';
import { AuthShell, Field } from './AuthShell';
import { Button } from '../../components/ui/Button';
import { useAuth } from '../../context/AuthContext';

const roles = [
  { id: 'farmer', label: 'کشاورز' },
  { id: 'rancher', label: 'دامدار' },
  { id: 'researcher', label: 'پژوهشگر' },
  { id: 'student', label: 'دانشجو' },
  { id: 'business', label: 'تجاری' },
  { id: 'org', label: 'سازمانی' },
];

export const RegisterPage: React.FC = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: '', phone: '', role: 'farmer', pass: '', confirm: '' });
  const [terms, setTerms] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.pass !== form.confirm) { setError('رمز عبور و تکرار آن یکسان نیست'); return; }
    if (!terms) { setError('لطفاً قوانین و حریم خصوصی را بپذیرید'); return; }
    setError(''); setBusy(true);
    try {
      await register({ name: form.name, email: form.email, role: form.role });
      navigate('/hydroma');
    } catch (err: any) { setError(err.message); } finally { setBusy(false); }
  };

  return (
    <AuthShell title="ایجاد حساب رایگان" subtitle="کشاورز، دامدار، پژوهشگر یا دانشجو — همه رایگان">
      <form onSubmit={submit}>
        {error && <div className="badge badge-error" style={{ width: '100%', justifyContent: 'center', marginBottom: '1rem', padding: '0.6rem' }}>{error}</div>}

        <Field label="نام و نام خانوادگی">
          <input className="input" required value={form.name} onChange={e => set('name', e.target.value)} placeholder="مثلاً: سارا محمدی" />
        </Field>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
          <Field label="ایمیل">
            <input className="input" dir="ltr" style={{ textAlign: 'left' }} type="email" required value={form.email} onChange={e => set('email', e.target.value)} placeholder="you@farm.ir" />
          </Field>
          <Field label="موبایل">
            <input className="input" dir="ltr" style={{ textAlign: 'left' }} type="tel" value={form.phone} onChange={e => set('phone', e.target.value)} placeholder="+98 9xx xxx xxxx" />
          </Field>
        </div>

        <Field label="نقش شما">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem' }}>
            {roles.map(r => (
              <button key={r.id} type="button" onClick={() => set('role', r.id)}
                className={form.role === r.id ? 'btn btn-primary' : 'btn btn-secondary'}
                style={{ padding: '0.6rem 0.4rem', fontSize: '0.8rem' }}>
                {r.label}
              </button>
            ))}
          </div>
        </Field>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
          <Field label="رمز عبور">
            <input className="input" dir="ltr" style={{ textAlign: 'left' }} type="password" required minLength={8} value={form.pass} onChange={e => set('pass', e.target.value)} />
          </Field>
          <Field label="تکرار رمز">
            <input className="input" dir="ltr" style={{ textAlign: 'left' }} type="password" required minLength={8} value={form.confirm} onChange={e => set('confirm', e.target.value)} />
          </Field>
        </div>

        <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '1.4rem', cursor: 'pointer' }}>
          <input type="checkbox" checked={terms} onChange={e => setTerms(e.target.checked)} />
          <span><Link to="/terms" style={{ color: 'var(--color-primary)' }}>قوانین</Link> و <Link to="/privacy" style={{ color: 'var(--color-primary)' }}>حریم خصوصی</Link> را می‌پذیرم</span>
        </label>

        <Button variant="primary" size="lg" loading={busy} style={{ width: '100%' }}>ثبت‌نام</Button>

        <p style={{ textAlign: 'center', marginTop: '1.4rem', fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
          حساب دارید؟ <Link to="/login" style={{ color: 'var(--color-primary)', fontWeight: 700 }}>ورود</Link>
        </p>
      </form>
    </AuthShell>
  );
};
''')

    wf(base / "ForgotPasswordPage.tsx", r'''import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, CheckCircle2 } from 'lucide-react';
import { AuthShell, Field } from './AuthShell';
import { Button } from '../../components/ui/Button';

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true);
    await new Promise(r => setTimeout(r, 900));
    setBusy(false); setSent(true);
  };

  return (
    <AuthShell title="بازیابی رمز عبور" subtitle="لینک بازیابی به ایمیل شما ارسال می‌شود">
      {sent ? (
        <div style={{ textAlign: 'center', padding: '1rem 0' }}>
          <CheckCircle2 size={56} className="animate-float" style={{ color: 'var(--color-success)', margin: '0 auto 1rem' }} />
          <h3 style={{ marginBottom: '0.5rem' }}>ایمیل ارسال شد</h3>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            لینک بازیابی به {email} ارسال شد. صندوق ورودی را بررسی کنید.
          </p>
          <Link to="/login"><Button variant="primary" style={{ width: '100%' }}>بازگشت به ورود</Button></Link>
        </div>
      ) : (
        <form onSubmit={submit}>
          <Field label="ایمیل ثبت‌شده">
            <div style={{ position: 'relative' }}>
              <Mail size={16} style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-tertiary)' }} />
              <input className="input" dir="ltr" style={{ paddingRight: '2.4rem', textAlign: 'left' }} type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="you@farm.ir" />
            </div>
          </Field>
          <Button variant="primary" size="lg" loading={busy} style={{ width: '100%' }}>ارسال لینک بازیابی</Button>
          <p style={{ textAlign: 'center', marginTop: '1.4rem', fontSize: '0.9rem' }}>
            <Link to="/login" style={{ color: 'var(--color-primary)', fontWeight: 700 }}>بازگشت به ورود</Link>
          </p>
        </form>
      )}
    </AuthShell>
  );
};
''')
    log("صفحات Auth (ورود/ثبت‌نام/فراموشی)")

# ═══════════════ 8) Pricing (USDT) ═══════════════
def build_pricing():
    wf(FE / "src/pages/PricingPage.tsx", r'''import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, X, Copy, Wallet, ShieldCheck, Sparkles } from 'lucide-react';
import { PublicLayout } from '../components/layout/PublicLayout';
import { Button } from '../components/ui/Button';

interface Plan {
  id: string; name: string; audience: string; price: number; period: string;
  color: string; highlight?: boolean; features: { text: string; ok: boolean }[];
}

const plans: Plan[] = [
  {
    id: 'farmer', name: 'کشاورز و دامدار', audience: 'رایگان برای همیشه', price: 0, period: 'USDT / سال', color: '#22c55e',
    features: [
      { text: 'تا ۵ هکتار زمین و ۵۰ رأس دام', ok: true },
      { text: 'برنامه کشت و بودجه آب پایه', ok: true },
      { text: 'هشدارهای اقلیمی محلی', ok: true },
      { text: 'دسترسی به بازارچه محلی (کارمزد ۵٪)', ok: true },
      { text: 'پشتیبانی انجمن', ok: true },
      { text: 'پایش ماهواره‌ای NDVI', ok: false },
      { text: 'صدور اعتبار کربن', ok: false },
    ],
  },
  {
    id: 'research', name: 'پژوهشگر و دانشجو', audience: 'رایگان با ایمیل دانشگاهی', price: 0, period: 'USDT / سال', color: '#3b82f6',
    features: [
      { text: 'دسترسی کامل به شبیه‌سازها', ok: true },
      { text: 'خروجی داده CSV / JSON', ok: true },
      { text: 'API روزانه ۱۰۰ درخواست', ok: true },
      { text: 'دسترسی به داده‌های باز', ok: true },
      { text: 'مجوز استناد علمی', ok: true },
      { text: 'استفاده تجاری', ok: false },
    ],
  },
  {
    id: 'pro', name: 'تجاری / حرفه‌ای', audience: 'برای کسب‌وکارهای کشاورزی', price: 240, period: 'USDT / سال', color: '#f59e0b', highlight: true,
    features: [
      { text: 'زمین و دام نامحدود', ok: true },
      { text: 'شبیه‌سازی پیشرفته + سه‌بعدی', ok: true },
      { text: 'پایش ماهواره‌ای NDVI روزانه', ok: true },
      { text: 'صدور اعتبار کربن (کارمزد ۲٪)', ok: true },
      { text: 'API روزانه ۱۰,۰۰۰ درخواست', ok: true },
      { text: 'پشتیبانی اولویت‌دار ۲۴/۷', ok: true },
    ],
  },
  {
    id: 'org', name: 'سازمانی / Enterprise', audience: 'دولت‌ها، NGOها، هلدینگ‌ها', price: 2400, period: 'USDT / سال', color: '#8b5cf6',
    features: [
      { text: 'کاربران نامحدود + SSO', ok: true },
      { text: 'برند اختصاصی (White-label)', ok: true },
      { text: 'زیرساخت اختصاصی + SLA 99.9%', ok: true },
      { text: 'مشاور اختصاصی و آموزش تیم', ok: true },
      { text: 'API نامحدود', ok: true },
      { text: 'گزارش‌های سازمانی سفارشی', ok: true },
    ],
  },
];

const USDT_ADDRESS = 'TQmEcoNojinHyDroMaUsdtTrc20XXXXXXXXX';

export const PricingPage: React.FC = () => {
  const [selected, setSelected] = useState<Plan | null>(null);
  const [network, setNetwork] = useState('TRC-20');
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(USDT_ADDRESS);
    setCopied(true); setTimeout(() => setCopied(false), 1500);
  };

  return (
    <PublicLayout>
      <section style={{ padding: '7rem 2rem 5rem', maxWidth: 1400, margin: '0 auto' }}>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ textAlign: 'center', marginBottom: '4rem' }}>
          <h1 style={{ fontSize: '2.8rem', fontWeight: 800, marginBottom: '1rem' }}>قیمت‌گذاری شفاف</h1>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '1.1rem', maxWidth: 700, margin: '0 auto 1.5rem' }}>
            کشاورزان، دامداران، پژوهشگران و دانشجویان <strong className="gradient-text">رایگان</strong>.
            استفاده تجاری و سازمانی با پرداخت رمزارز.
          </p>
          <div className="badge badge-info" style={{ padding: '0.6rem 1.2rem', fontSize: '0.85rem' }}>
            <ShieldCheck size={16} /> پرداخت‌ها فقط با تتر (USDT) یا رمزارز معتبر — بدون ارز ملی
          </div>
        </motion.div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(270px, 1fr))', gap: '1.75rem', alignItems: 'stretch' }}>
          {plans.map((p, i) => (
            <motion.div key={p.id}
              initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}
              whileHover={{ y: -10 }}
              className="card"
              style={{ position: 'relative', borderTop: `4px solid ${p.color}`, padding: '2rem', display: 'flex', flexDirection: 'column', boxShadow: p.highlight ? `0 20px 50px ${p.color}33` : undefined }}>
              {p.highlight && (
                <span className="badge" style={{ position: 'absolute', top: -14, right: '50%', transform: 'translateX(50%)', background: p.color, color: '#fff', padding: '0.4rem 1rem' }}>
                  <Sparkles size={12} /> پیشنهاد ما
                </span>
              )}
              <h3 style={{ fontSize: '1.3rem', fontWeight: 800 }}>{p.name}</h3>
              <p style={{ color: 'var(--color-text-tertiary)', fontSize: '0.85rem', marginBottom: '1.25rem' }}>{p.audience}</p>
              <div style={{ marginBottom: '1.5rem', direction: 'ltr', textAlign: 'left' }}>
                <span style={{ fontSize: '2.6rem', fontWeight: 800, color: p.color }}>{p.price}</span>
                <span style={{ color: 'var(--color-text-tertiary)', fontSize: '0.85rem' }}> {p.period}</span>
              </div>
              <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 1.75rem', flex: 1 }}>
                {p.features.map((f, j) => (
                  <li key={j} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', marginBottom: '0.7rem', fontSize: '0.9rem', color: f.ok ? 'var(--color-text-secondary)' : 'var(--color-text-tertiary)', textDecoration: f.ok ? 'none' : 'line-through' }}>
                    {f.ok ? <Check size={16} style={{ color: p.color, flexShrink: 0, marginTop: 2 }} /> : <X size={16} style={{ flexShrink: 0, marginTop: 2 }} />}
                    {f.text}
                  </li>
                ))}
              </ul>
              <Button variant={p.highlight ? 'primary' : 'secondary'} onClick={() => setSelected(p)} style={{ width: '100%' }}>
                {p.price === 0 ? 'شروع رایگان' : 'پرداخت با تتر'}
              </Button>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Crypto payment modal */}
      <AnimatePresence>
        {selected && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={() => setSelected(null)}
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
            <motion.div onClick={e => e.stopPropagation()}
              initial={{ scale: 0.9, y: 30 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.9, y: 30 }}
              className="card" style={{ maxWidth: 440, width: '100%', padding: '2rem' }}>
              <h3 style={{ marginBottom: '0.5rem' }}>پرداخت {selected.name}</h3>
              <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem', marginBottom: '1.25rem' }}>
                مبلغ: <strong style={{ color: selected.color }}>{selected.price} USDT</strong> در سال
              </p>

              <p style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem' }}>انتخاب شبکه:</p>
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem' }}>
                {['TRC-20', 'ERC-20', 'BEP-20'].map(n => (
                  <button key={n} onClick={() => setNetwork(n)} className={network === n ? 'btn btn-primary' : 'btn btn-secondary'} style={{ padding: '0.5rem 0.9rem', fontSize: '0.8rem' }}>{n}</button>
                ))}
              </div>

              <p style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem' }}>آدرس کیف پول ({network}):</p>
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                <code className="input" dir="ltr" style={{ flex: 1, fontSize: '0.75rem', fontFamily: 'monospace' }}>{USDT_ADDRESS}</code>
                <Button variant="secondary" onClick={copy} icon={<Copy size={14} />}>{copied ? 'کپی شد' : ''}</Button>
              </div>

              <div className="badge badge-warning" style={{ width: '100%', justifyContent: 'center', padding: '0.7rem', marginBottom: '1.25rem' }}>
                <Wallet size={14} /> فقط USDT / BTC / ETH — ارز ملی پذیرفته نمی‌شود
              </div>

              <Button variant="primary" style={{ width: '100%' }}>تأیید پرداخت و فعال‌سازی</Button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </PublicLayout>
  );
};
''')
    log("PricingPage.tsx (4 سطح + USDT)")

# ═══════════════ 9) Terms / Privacy / Blog ═══════════════
def build_static_pages():
    wf(FE / "src/pages/TermsPage.tsx", r'''import React from 'react';
import { PublicLayout } from '../components/layout/PublicLayout';

const sections = [
  ['۱. پذیرش شرایط', 'با استفاده از پلتفرم Eco Nojin × HyDroMa، این شرایط را می‌پذیرید. در صورت عدم پذیرش، از استفاده خودداری کنید.'],
  ['۲. حساب کاربری', 'مسئولیت حفظ محرمانگی رمز عبور با شماست. هر فعالیت تحت حساب شما، مسئولیت شماست.'],
  ['۳. سطوح دسترسی', 'سطح رایگان (کشاورز، دامدار، پژوهشگر، دانشجو) صرفاً برای استفاده غیرتجاری است. استفاده تجاری نیازمند طرح تجاری یا سازمانی است.'],
  ['۴. پرداخت‌ها', 'کلیه پرداخت‌ها صرفاً با رمزارز معتبر (USDT، BTC، ETH) انجام می‌شود. هیچ ارز ملی پذیرفته نمی‌شود. پرداخت‌ها غیرقابل برگشت هستند مگر در موارد نقض سرویس توسط ما.'],
  ['۵. داده و مالکیت', 'داده‌های واردشده توسط شما متعلق به شماست. ما فقط برای ارائه سرویس پردازش می‌کنیم. داده‌های تجمیعی بی‌نام برای بهبود مدل‌ها استفاده می‌شود.'],
  ['۶. اعتبار کربن', 'صدور اعتبار کربن بر اساس مدل‌های علمی است و تضمین قیمت بازار نمی‌شود. کارمزد پلتفرم ۲٪ است.'],
  ['۷. سلب مسئولیت', 'نتایج شبیه‌سازی جنبه مشورتی دارند و جایگزین توصیه کارشناس رسمی نیستند.'],
  ['۸. فسخ', 'در صورت نقض شرایط، امکان تعلیق حساب وجود دارد. شما هر زمان می‌توانید حساب را حذف کنید.'],
];

export const TermsPage: React.FC = () => (
  <PublicLayout>
    <section style={{ maxWidth: 860, margin: '0 auto', padding: '7rem 2rem 5rem' }}>
      <h1 style={{ fontSize: '2.5rem', fontWeight: 800, marginBottom: '2.5rem', textAlign: 'center' }}>قوانین و شرایط استفاده</h1>
      {sections.map(([t, b], i) => (
        <div key={i} className="card" style={{ marginBottom: '1.25rem', padding: '1.75rem' }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '0.75rem' }}>{t}</h3>
          <p style={{ color: 'var(--color-text-secondary)', lineHeight: 1.9, margin: 0 }}>{b}</p>
        </div>
      ))}
    </section>
  </PublicLayout>
);
''')

    wf(FE / "src/pages/PrivacyPage.tsx", r'''import React from 'react';
import { ShieldCheck, Lock, EyeOff, Database } from 'lucide-react';
import { PublicLayout } from '../components/layout/PublicLayout';

const items = [
  { icon: Lock, t: 'رمزنگاری سرتاسری', b: 'داده‌ها در انتقال (TLS) و در ذخیره‌سازی (AES-256) رمزنگاری می‌شوند.' },
  { icon: EyeOff, t: 'عدم فروش داده', b: 'داده شخصی شما هرگز به اشخاص ثالث فروخته نمی‌شود.' },
  { icon: Database, t: 'حداقل داده', b: 'فقط داده‌های لازم برای ارائه سرویس جمع‌آوری می‌شود.' },
  { icon: ShieldCheck, t: 'حق فراموشی', b: 'هر زمان بخواهید، داده‌های شما به‌طور کامل حذف می‌شود.' },
];

export const PrivacyPage: React.FC = () => (
  <PublicLayout>
    <section style={{ maxWidth: 960, margin: '0 auto', padding: '7rem 2rem 5rem' }}>
      <h1 style={{ fontSize: '2.5rem', fontWeight: 800, marginBottom: '1rem', textAlign: 'center' }}>حریم خصوصی</h1>
      <p style={{ textAlign: 'center', color: 'var(--color-text-secondary)', marginBottom: '3rem' }}>حریم شما، خط قرمز ماست.</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.5rem' }}>
        {items.map((it, i) => {
          const Icon = it.icon;
          return (
            <div key={i} className="card" style={{ padding: '1.75rem' }}>
              <Icon size={32} style={{ color: 'var(--color-primary)', marginBottom: '1rem' }} />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.6rem' }}>{it.t}</h3>
              <p style={{ color: 'var(--color-text-secondary)', lineHeight: 1.8, margin: 0 }}>{it.b}</p>
            </div>
          );
        })}
      </div>
    </section>
  </PublicLayout>
);
''')

    wf(FE / "src/pages/BlogPage.tsx", r'''import React from 'react';
import { motion } from 'framer-motion';
import { Clock, Tag } from 'lucide-react';
import { PublicLayout } from '../components/layout/PublicLayout';

const posts = [
  { title: 'چگونه بادشکن ۶۰٪ فرسایش بادی را کاهش می‌دهد؟', cat: 'فرسایش', color: '#f59e0b', time: '۶ دقیقه', date: '۱۴۰۵/۰۶/۰۱' },
  { title: 'راهنمای کامل کشت چندلایه (Agroforestry)', cat: 'کشاورزی', color: '#22c55e', time: '۹ دقیقه', date: '۱۴۰۵/۰۵/۲۰' },
  { title: 'اعتبار کربن چیست و چگونه درآمدزایی کنیم؟', cat: 'کربن', color: '#10b981', time: '۷ دقیقه', date: '۱۴۰۵/۰۵/۱۰' },
  { title: 'NDVI از فضا: پایش سلامت گیاه با ماهواره', cat: 'ماهواره', color: '#0ea5e9', time: '۵ دقیقه', date: '۱۴۰۵/۰۴/۲۸' },
  { title: 'بودجه آب مزرعه: نفوذ، رواناب، آبخوان', cat: 'آب', color: '#3b82f6', time: '۸ دقیقه', date: '۱۴۰۵/۰۴/۱۵' },
  { title: 'اقتصاد گله: سودآوری واقعی دامداری', cat: 'دامداری', color: '#b45309', time: '۶ دقیقه', date: '۱۴۵/۰/۰۲' },
];

export const BlogPage: React.FC = () => (
  <PublicLayout>
    <section style={{ maxWidth: 1200, margin: '0 auto', padding: '7rem 2rem 5rem' }}>
      <h1 style={{ fontSize: '2.5rem', fontWeight: 800, textAlign: 'center', marginBottom: '3rem' }}>وبلاگ Eco Nojin</h1>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.75rem' }}>
        {posts.map((p, i) => (
          <motion.article key={i} initial={{ opacity: 0, y: 25 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: (i % 3) * 0.1 }}
            whileHover={{ y: -8 }} className="card" style={{ overflow: 'hidden', padding: 0, cursor: 'pointer' }}>
            <div style={{ height: 140, background: `linear-gradient(135deg, ${p.color}, ${p.color}88)`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span className="badge" style={{ background: 'rgba(255,255,255,0.25)', color: '#fff', backdropFilter: 'blur(6px)' }}><Tag size={12} /> {p.cat}</span>
            </div>
            <div style={{ padding: '1.5rem' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.9rem', lineHeight: 1.6 }}>{p.title}</h3>
              <div style={{ display: 'flex', gap: '1rem', color: 'var(--color-text-tertiary)', fontSize: '0.8rem' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><Clock size={12} /> {p.time}</span>
                <span>{p.date}</span>
              </div>
            </div>
          </motion.article>
        ))}
      </div>
    </section>
  </PublicLayout>
);
''')
    log("Terms / Privacy / Blog")

# ═══════════════ 10) HyDroMa Dashboard ═══════════════
def build_hydroma():
    wf(FE / "src/pages/HydromaDashboard.tsx", r'''import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Droplets, Waves, CloudRain, Database, Wind, Leaf, LogOut, User } from 'lucide-react';
import { AnimatedLogo } from '../components/branding/AnimatedLogo';
import { StatCard } from '../components/ui/StatCard';
import { Button } from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';
import { toggleTheme } from '../hooks/useThemeMode';
import {
  WaterBudgetChart, CarbonForecastChart, ErosionRiskMap, LivestockEconomicsChart,
} from '../components/simulators';

export const HydromaDashboard: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <div className="hydroma-bg" style={{ minHeight: '100vh' }}>
      {/* Top bar */}
      <header className="glass" style={{ position: 'sticky', top: 0, zIndex: 50, padding: '0.9rem 2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border)' }}>
        <AnimatedLogo size="sm" showSubtitle={false} />
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Button variant="ghost" onClick={toggleTheme}>🌓</Button>
          <span className="badge badge-info"><User size={12} /> {user?.name}</span>
          <Button variant="ghost" onClick={logout} icon={<LogOut size={15} />}>خروج</Button>
        </div>
      </header>

      {/* Water hero */}
      <section style={{ position: 'relative', padding: '3.5rem 2rem 5rem', overflow: 'hidden', textAlign: 'center' }}>
        <div className="hydroma-waves" />
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ position: 'relative', zIndex: 1 }}>
          <motion.div animate={{ y: [0, -8, 0] }} transition={{ repeat: Infinity, duration: 4 }} style={{ display: 'inline-flex', color: '#7dd3fc', marginBottom: '1rem' }}>
            <Waves size={44} />
          </motion.div>
          <h1 style={{ fontSize: '2.2rem', fontWeight: 800, color: '#fff', marginBottom: '0.6rem' }}>
            خوش آمدی، {user?.name}
          </h1>
          <p style={{ color: '#bae6fd', fontSize: '1.05rem' }}>داشبورد هیدرولوژیک HyDroMa — آب، خاک، اقلیم</p>
        </motion.div>
      </section>

      <main style={{ maxWidth: 1400, margin: '-2rem auto 0', padding: '0 2rem 4rem', position: 'relative', zIndex: 2 }}>
        {/* Water stats */}
        <div className="grid grid-cols-4" style={{ marginBottom: '2rem' }}>
          <StatCard title="رطوبت خاک" value="۳۴٪" change={4.2} icon={<Droplets size={24} />} color="info" />
          <StatCard title="تبخیر-تعریق" value="۵.۲ mm" change={-2.1} icon={<Waves size={24} />} color="primary" />
          <StatCard title="رواناب" value="۱۲ mm" change={-15} icon={<CloudRain size={24} />} color="warning" />
          <StatCard title="تغذیه آبخوان" value="۸ mm" change={6.5} icon={<Database size={24} />} color="success" />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-2" style={{ marginBottom: '2rem' }}>
          <div className="card"><WaterBudgetChart /></div>
          <div className="card"><CarbonForecastChart years={20} initialSOC={1.5} /></div>
          <div className="card"><ErosionRiskMap windErosion={{ erosionTonHaYear: 15, riskLevel: 'high' }} waterErosion={{ soilLossTonHaYear: 8, riskLevel: 'high' }} /></div>
          <div className="card"><LivestockEconomicsChart herds={[
            { animalType: 'گاو', headCount: 20, revenue: 25000, feedCost: 8000, vetCost: 1000, laborCost: 3000, netProfit: 13000 },
            { animalType: 'گوسفند', headCount: 100, revenue: 18000, feedCost: 5000, vetCost: 1500, laborCost: 2000, netProfit: 9500 },
          ]} /></div>
        </div>

        {/* Quick actions */}
        <div className="card" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
          <Link to="/simulator"><Button variant="primary" icon={<Leaf size={16} />}>شبیه‌ساز کامل</Button></Link>
          <Link to="/pricing"><Button variant="secondary" icon={<Wind size={16} />}>ارتقای طرح</Button></Link>
        </div>
      </main>
    </div>
  );
};
''')
    log("HydromaDashboard.tsx (تم آب)")

# ═══════════════ 11) App.tsx routes ═══════════════
def build_app():
    wf(FE / "src/App.tsx", r'''import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { HomePage } from './pages/HomePage';
import { AboutPage } from './pages/AboutPage';
import { MissionPage } from './pages/MissionPage';
import { FeaturesPage } from './pages/FeaturesPage';
import { PricingPage } from './pages/PricingPage';
import { TermsPage } from './pages/TermsPage';
import { PrivacyPage } from './pages/PrivacyPage';
import { BlogPage } from './pages/BlogPage';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { ForgotPasswordPage } from './pages/auth/ForgotPasswordPage';
import { HydromaDashboard } from './pages/HydromaDashboard';
import { SimulatorDashboard } from './pages/SimulatorDashboard';
import './styles/global.css';

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/mission" element={<MissionPage />} />
        <Route path="/features" element={<FeaturesPage />} />
        <Route path="/pricing" element={<PricingPage />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/blog" element={<BlogPage />} />

        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />

        <Route path="/hydroma" element={<ProtectedRoute><HydromaDashboard /></ProtectedRoute>} />
        <Route path="/dashboard" element={<Navigate to="/hydroma" replace />} />
        <Route path="/simulator" element={<ProtectedRoute><SimulatorDashboard /></ProtectedRoute>} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
''')
    log("App.tsx (routes کامل)")

# ═══════════════ 12) CSS: scene + earth-dark + hydroma ═══════════════
def build_css():
    p = FE / "src/styles/global.css"
    css = p.read_text(encoding="utf-8")

    extra = r'''

/* ═══════════ حالت تاریک خاکی (Earth-Dark) ═══════════ */
[data-theme="dark"] {
  --color-bg: #141210;
  --color-surface: #1e1a16;
  --color-border: #33291f;
  --color-text-primary: #f3ede4;
  --color-text-secondary: #b8a992;
  --color-text-tertiary: #8a7a63;
}

/* ═══════════ انیمیشن‌های زنده ═══════════ */
@keyframes floatY { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-12px); } }
@keyframes drift { from { left: -25%; } to { left: 110%; } }
@keyframes rainfall { from { transform: translateY(-12vh); } to { transform: translateY(112vh); } }
@keyframes fly { 0% { left: -12vw; } 100% { left: 112vw; } }
@keyframes flap { 0%,100% { transform: scaleY(1); } 50% { transform: scaleY(0.45); } }
@keyframes waveMove { from { transform: translateX(0); } to { transform: translateX(-50%); } }
@keyframes twinkle { 0%,100% { opacity: 0.2; } 50% { opacity: 1; } }

.animate-float { animation: floatY 3.5s ease-in-out infinite; }
.animate-float-slow { animation: floatY 5s ease-in-out infinite; }

/* ═══════════ صحنه زنده ═══════════ */
.sky-light { background: linear-gradient(180deg, #cfe9ff 0%, #eaf6ff 45%, #eef8ec 100%); }
.sky-dark  { background: linear-gradient(180deg, #0b1020 0%, #171310 55%, #1e1a16 100%); }

.sun  { position: absolute; top: 9%; right: 12%; width: 92px; height: 92px; border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #fff7cc, #fbbf24 60%, #f59e0b);
  box-shadow: 0 0 70px 24px rgba(251,191,36,.45); animation: floatY 9s ease-in-out infinite; }
.moon { position: absolute; top: 9%; right: 12%; width: 72px; height: 72px; border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #f8fafc, #cbd5e1 70%);
  box-shadow: 0 0 46px 14px rgba(148,163,184,.35); animation: floatY 11s ease-in-out infinite; }

.star { position: absolute; border-radius: 50%; background: #e2e8f0; animation: twinkle 3s ease-in-out infinite; }

.cloud { position: absolute; left: -25%; width: 220px; height: 58px; border-radius: 60px;
  background: rgba(255,255,255,.9); filter: blur(2px); animation: drift linear infinite; }
.cloud::before, .cloud::after { content: ''; position: absolute; background: inherit; border-radius: 50%; }
.cloud::before { width: 92px; height: 92px; top: -42px; left: 30px; }
.cloud::after  { width: 70px; height: 70px; top: -28px; right: 36px; }
[data-theme="dark"] .cloud { background: rgba(90,100,125,.28); }

.raindrop { position: absolute; top: -12vh; width: 2px; height: 13vh; border-radius: 2px;
  background: linear-gradient(180deg, transparent, rgba(59,130,246,.55)); animation: rainfall linear infinite; }

.bird { position: absolute; left: -12vw; width: 46px; color: #475569; animation: fly linear infinite; }
.bird path { animation: flap .55s ease-in-out infinite; transform-origin: center; }
[data-theme="dark"] .bird { color: #94a3b8; }

.hill { position: absolute; bottom: 90px; left: 0; right: 0; width: 100%; }

.water { position: absolute; left: 0; right: 0; bottom: 0; height: 110px; overflow: hidden; }
.wave { position: absolute; bottom: 0; left: 0; width: 200%; height: 100%; animation: waveMove 16s linear infinite; }
.wave.w2 { opacity: .55; animation-duration: 24s; animation-direction: reverse; }

/* ═══════════ داشبورد HyDroMa ═══════════ */
.hydroma-bg { background: linear-gradient(180deg, #0c4a6e 0%, #075985 30%, var(--color-bg) 75%); }
.hydroma-waves { position: absolute; inset: auto 0 0 0; height: 120px;
  background:
    radial-gradient(120% 60% at 50% 100%, rgba(125,211,252,.35), transparent 60%);
}
.hydroma-waves::before, .hydroma-waves::after { content: ''; position: absolute; left: -50%; right: -50%; height: 200%;
  border-radius: 45%; animation: spin 18s linear infinite; }
.hydroma-waves::before { top: 40%; background: rgba(12,74,110,.5); }
.hydroma-waves::after  { top: 45%; background: rgba(7,89,133,.6); animation-duration: 26s; }
@keyframes spin { from { transform: rotate(0); } to { transform: rotate(360deg); } }
'''
    if 'Earth-Dark' not in css:
        css += extra
        p.write_text(css, encoding="utf-8")
    log("global.css (صحنه زنده + تاریک خاکی + HyDroMa)")

# ═══════════════ 13) PublicHeader update (logo + nav) ═══════════════
def build_public_header():
    wf(FE / "src/components/layout/PublicHeader.tsx", r'''import React, { useState, useEffect } from 'react';
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
    <motion.header initial={{ y: -80 }} animate={{ y: 0 }}
      style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100, padding: '0.9rem 2rem',
        background: scrolled ? 'var(--color-surface)' : 'transparent',
        backdropFilter: scrolled ? 'blur(12px)' : 'none',
        borderBottom: scrolled ? '1px solid var(--color-border)' : 'none', transition: 'all .3s' }}>
      <div style={{ maxWidth: 1400, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
        <AnimatedLogo size="sm" showSubtitle={false} />

        <nav style={{ display: 'flex', gap: '1.75rem' }} className="hidden md:flex">
          {navItems.map(n => (
            <Link key={n.id} to={n.href} style={{ color: 'var(--color-text-secondary)', textDecoration: 'none', fontSize: '0.95rem', fontWeight: 500 }}
              onMouseEnter={e => (e.currentTarget.style.color = 'var(--color-primary)')}
              onMouseLeave={e => (e.currentTarget.style.color = 'var(--color-text-secondary)')}>
              {n.label}
            </Link>
          ))}
        </nav>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Button variant="ghost" onClick={toggleTheme}>{theme === 'light' ? '🌙' : '☀️'}</Button>
          {user ? (
            <Link to="/hydroma"><Button variant="primary">داشبورد</Button></Link>
          ) : (
            <>
              <Link to="/login" className="hidden md:block"><Button variant="secondary">ورود</Button></Link>
              <Link to="/register" className="hidden md:block"><Button variant="primary">ثبت‌نام رایگان</Button></Link>
            </>
          )}
          <button className="md:hidden btn btn-ghost" onClick={() => setOpen(!open)} style={{ padding: '0.5rem' }}>
            {open ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {open && (
        <motion.div initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }}
          style={{ position: 'absolute', top: '100%', left: 0, right: 0, background: 'var(--color-surface)', borderBottom: '1px solid var(--color-border)', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {navItems.map(n => <Link key={n.id} to={n.href} onClick={() => setOpen(false)} style={{ color: 'var(--color-text-primary)', textDecoration: 'none', padding: '0.7rem', borderRadius: 'var(--radius-lg)' }}>{n.label}</Link>)}
          <Link to="/login" onClick={() => setOpen(false)}><Button variant="secondary" style={{ width: '100%' }}>ورود</Button></Link>
          <Link to="/register" onClick={() => setOpen(false)}><Button variant="primary" style={{ width: '100%' }}>ثبت‌نام رایگان</Button></Link>
        </motion.div>
      )}
    </motion.header>
  );
};
''')
    log("PublicHeader (لوگوی هوشمند + nav)")

def main():
    print("\n" + "=" * 70)
    print("  🌍 Eco Nojin - تجربه کلاس جهانی")
    print("=" * 70 + "\n")
    backup()
    build_hook()
    build_background()
    build_logo()
    build_auth()
    build_module_card()
    build_home()
    build_auth_pages()
    build_pricing()
    build_static_pages()
    build_hydroma()
    build_app()
    build_css()
    build_public_header()

    print("\n" + "=" * 70)
    print("  ✅ تکمیل شد!")
    print("=" * 70)
    print("""
  🎨 لوگو: Eco Nojin -> خانه | HyDroMa -> داشبورد
  🌦️ پس‌زمینه زنده: آب + ابر + باران + پرنده (روشن/تاریک)
  🌑 تاریک خاکی: تُن‌های تیره + خاک
   ۱۰ کارت ماژول رنگی (با قفل ورود)
  🔐 ورود / ثبت‌نام / فراموشی رمز (انیمیشن زنده)
  💰 قیمت‌گذاری ۴ سطح + پرداخت فقط USDT/کریپتو
  📄 قوانین / حریم خصوصی / وبلاگ
  💧 داشبورد HyDroMa با تم آب

  🚀 اجرا:
     cd frontend && pnpm run dev

  📍 مسیرها:
     /            صفحه خانه زنده
     /login       ورود (دمو: هر ایمیل + رمز ۶+ کاراکتر)
     /register    ثبت‌نام با ۶ نقش
     /pricing     قیمت‌گذاری + مودال USDT
     /hydroma     داشبورد HyDroMa (نیاز به ورود)
     /simulator   شبیه‌ساز (نیاز به ورود)
""")

if __name__ == "__main__":
    main()