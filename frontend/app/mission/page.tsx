'use client';
import Footer from '../../components/layout/Footer';
import { useI18n } from '../../lib/i18n-context';
import { useTheme } from '../../lib/theme-context';
import { useBreakpoint } from '../../lib/use-breakpoint';
import { motion } from 'framer-motion';
import {
  Leaf, Droplet, Users, Mountain, Sprout,
  Heart, Target, Award, ArrowRight, Sparkles,
  TrendingDown, TreePine, Scale, HandHeart
} from 'lucide-react';

export default function MissionPage() {
  const { t, direction } = useI18n();
  const { colors, theme } = useTheme();
  const { isMobile } = useBreakpoint();

  // Global crisis stats (verified sources: UNCCD, FAO, IPCC, WRI, World Bank)
  const globalStats = [
    { value: '40%', key: 'stat_degraded_land', icon: TrendingDown, color: '#f97316', source: 'UNCCD 2024' },
    { value: '2B+', key: 'stat_water_stress', icon: Droplet, color: '#0ea5e9', source: 'WRI 2024' },
    { value: '41%', key: 'stat_drylands', icon: Mountain, color: '#fbbf24', source: 'UNCCD 2023' },
    { value: '216M', key: 'stat_climate_migrants', icon: Users, color: '#fb7185', source: 'World Bank 2021' },
  ];

  const sixApproaches = [
    {
      icon: Sprout,
      title: { en: 'Climate-Smart Agriculture (CSA)', fa: 'کشاورزی هوشمند اقلیم (CSA)' },
      desc: {
        en: 'Increase production resilience and food security while reducing greenhouse gas emissions (FAO, 2021).',
        fa: 'افزایش تاب‌آوری تولید و امنیت غذایی هم‌زمان با کاهش انتشار گازهای گلخانه‌ای (FAO, 2021).',
      },
      color: '#16a34a',
    },
    {
      icon: Droplet,
      title: { en: 'Integrated Water Resources Management (IWRM)', fa: 'مدیریت یکپارچه منابع آب (IWRM)' },
      desc: {
        en: 'Restore hydrological balance through simultaneous demand and supply management at basin scale (GWP, 2009).',
        fa: 'بازگرداندن تعادل به چرخه هیدرولوژیک از طریق مدیریت هم‌زمان تقاضا و عرضه در مقیاس حوضه (GWP, 2009).',
      },
      color: '#0ea5e9',
    },
    {
      icon: Leaf,
      title: { en: 'Sustainable Land Management (SLM)', fa: 'مدیریت پایدار زمین (SLM)' },
      desc: {
        en: 'Restore soil structure, increase soil organic carbon (SOC), and halt erosion (UNCCD, 2017).',
        fa: 'ترمیم ساختار خاک، افزایش کربن آلی (SOC) و توقف فرسایش (UNCCD, 2017).',
      },
      color: '#f97316',
    },
    {
      icon: TreePine,
      title: { en: 'Land Degradation Neutrality (LDN)', fa: 'خنثی‌سازی تخریب سرزمین (LDN)' },
      desc: {
        en: 'Macro goal framework to balance degradation and restoration of lands globally.',
        fa: 'چتر هدف‌گذار کلان برای دستیابی به تعادل بین تخریب و احیای اراضی در سطح جهانی.',
      },
      color: '#fbbf24',
    },
    {
      icon: Mountain,
      title: { en: 'Nature-Based Solutions (NbS)', fa: 'راهکارهای مبتنی بر طبیعت (NbS)' },
      desc: {
        en: 'Replace rigid concrete structures with low-cost, flexible ecological engineering (IUCN).',
        fa: 'جایگزینی سازه‌های صلب و پرهزینه بتنی با مهندسی اکولوژیک کم‌هزینه و انطباق‌پذیر (IUCN).',
      },
      color: '#0d9488',
    },
    {
      icon: HandHeart,
      title: { en: 'Multi-Level Participatory Governance', fa: 'حکمرانی مشارکتی چندسطحی' },
      desc: {
        en: 'Transfer decision-making power and benefit distribution to local communities and landscape-level institutions.',
        fa: 'انتقال بخشی از قدرت تصمیم‌گیری و توزیع منافع به عرصه منظر و جوامع محلی.',
      },
      color: '#fb7185',
    },
  ];

  const threeMessages = [
    {
      icon: Users,
      audience: { en: 'To Local Communities', fa: 'به جوامع محلی' },
      subtitle: {
        en: 'From crisis management to sustainable ownership',
        fa: 'از مدیریت بحران تا مالکیت پایدار',
      },
      text: {
        en: 'We know how recent years have weighed on you—less water, exhausted soils, unstable incomes. Hydroma Nojin is not a distant plan; it is a tool to return decision-making power and livelihoods to your hands. Combining your indigenous knowledge (qanats, water-sharing, community labor) with low-cost technologies (biological terraces, infiltration pits, agroforestry), we lock water in the soil and return the soil to your farm. You are not a beneficiary—you are the architect and owner of your land restoration.',
        fa: 'ما می‌دانیم که سال‌های اخیر چگونه بر دوش شما سنگینی کرده است؛ آب کمتر، خاک خسته‌تر، و درآمد ناپایدارتر. هیدروما نوژین یک طرح از راه دور نیست؛ بلکه ابزاری است برای بازگرداندن قدرت تصمیم‌گیری و معیشت به دستان شما. ما با تکیه بر دانش بومی شما (قنات، میرابی، بُنه‌ها) و ترکیب آن با فناوری‌های کم‌هزینه (تراس‌های بیولوژیک، چاله‌های نفوذی، آگروفارستری)، آب را در خاک حبس کرده و خاک را به مزرعه شما برمی‌گردانیم. در این طرح، شما نه یک بهره‌بر، بلکه معمار و مالک اصلی احیای سرزمین خود هستید.',
      },
      color: '#f97316',
    },
    {
      icon: Award,
      audience: { en: 'To the Scientific & Technical Community', fa: 'به جامعه علمی-فنی' },
      subtitle: {
        en: 'A living laboratory of paradigm transition',
        fa: 'آزمایشگاه زنده گذار پارادایمی',
      },
      text: {
        en: 'Hydroma Nojin is a platform for moving from siloed projects to landscape-centered engineering. We invite you to take hydrological models (SWAT+), biophysical models (AquaCrop), and carbon dynamics models (RothC) out of academia and calibrate them across diverse climates—from Sahel to Central Asia to the Andes. Our challenge is data triangulation: combining remote sensing (Sentinel-2), low-cost IoT sensors, and citizen science. You are not designing structures; you are designing resilient socio-ecological systems.',
        fa: 'هیدروما نوژین بستری است برای عبور از پروژه‌های جزیره‌ای و حرکت به سمت «مهندسی منظرمحور». ما از شما می‌خواهیم مدل‌های هیدرولوژیک (SWAT+)، بیوفیزیکی (AquaCrop) و دینامیک کربن (RothC) را از محیط آکادمیک خارج کرده و در اقلیم‌های متنوع جهان (از ساحل تا آسیای میانه تا آند) کالیبره و عملیاتی کنید. چالش ما «تثلیث داده‌ای» است؛ ترکیب سنجش‌ازدور، سنسورهای IoT کم‌هزینه و پایش مشارکتی شهروندی. شما طراح سازه نیستید؛ بلکه طراح سیستم‌های تاب‌آور اجتماعی-اکولوژیک هستید.',
      },
      color: '#0ea5e9',
    },
    {
      icon: Scale,
      audience: { en: 'To Policymakers & Investors', fa: 'به سیاست‌گذاران و سرمایه‌گذاران' },
      subtitle: {
        en: 'A platform for synergizing policy, capital, and international commitments',
        fa: 'پلتفرم هم‌افزایی سیاست، سرمایه و تعهدات بین‌المللی',
      },
      text: {
        en: 'Continuing siloed approaches imposes hidden costs—soil erosion, climate migration, aquifer collapse—on public budgets. Hydroma Nojin is an impact investment package that, at optimized cost (< $1000/ha), simultaneously addresses six fronts of your national and international commitments: NDC targets, SDGs, migration control, food security, biodiversity, and rural stability. Through landscape agreements, we bridge bureaucratic gaps between ministries; through blended finance, we de-risk private investment. Supporting Hydroma is investing in natural infrastructure and human dignity.',
        fa: 'ادامه رویکرد بخشی، هزینه‌های پنهان فرسایش خاک، مهاجرت اقلیمی و فروپاشی آبخوان‌ها را به بودجه عمومی تحمیل می‌کند. هیدروما نوژین یک «بسته سرمایه‌گذاری اثرگذار» است که با هزینه‌ای بهینه (کمتر از ۱۰۰۰ دلار/هکتار)، هم‌زمان شش جبهه از تعهدات ملی و بین‌المللی شما را هدف قرار می‌دهد: از اهداف NDC و SDGs گرفته تا کنترل مهاجرت و امنیت غذایی. این طرح با ایجاد «توافق‌نامه‌های منظر»، گسل‌های بوروکراتیک بین وزارتخانه‌ها را پر کرده و با مدل تأمین مالی ترکیبی، ریسک سرمایه‌گذاری بخش خصوصی را کاهش می‌دهد. حمایت از هیدروما، سرمایه‌گذاری بر روی زیرساخت طبیعی و کرامت انسانی است.',
      },
      color: '#fbbf24',
    },
  ];

  const container = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };
  const item = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } };

  const getLocalized = (obj: any) => obj[t('locale') as keyof typeof obj] || obj.en || Object.values(obj)[0];

  return (
    <div dir={direction} style={{ background: colors.bg, minHeight: '100vh' }}>
      {/* Hero */}
      <section style={{
        padding: isMobile ? '80px 20px 60px' : '120px 48px 80px',
        background: theme === 'dark'
          ? 'radial-gradient(ellipse at top, rgba(249, 115, 22, 0.15), transparent 60%), #0c0a09'
          : 'radial-gradient(ellipse at top, rgba(249, 115, 22, 0.1), transparent 60%), #fffbeb',
        position: 'relative',
        overflow: 'hidden',
      }}>
        <motion.div
          animate={{ y: [0, -20, 0] }}
          transition={{ duration: 8, repeat: Infinity }}
          style={{
            position: 'absolute', top: '10%', left: '10%',
            width: '300px', height: '300px',
            background: 'radial-gradient(circle, rgba(249, 115, 22, 0.2), transparent 70%)',
            borderRadius: '50%', filter: 'blur(40px)', pointerEvents: 'none',
          }}
        />
        <motion.div
          animate={{ y: [0, 20, 0] }}
          transition={{ duration: 10, repeat: Infinity }}
          style={{
            position: 'absolute', bottom: '10%', right: '10%',
            width: '400px', height: '400px',
            background: 'radial-gradient(circle, rgba(14, 165, 233, 0.15), transparent 70%)',
            borderRadius: '50%', filter: 'blur(40px)', pointerEvents: 'none',
          }}
        />

        <div style={{ maxWidth: '1100px', margin: '0 auto', textAlign: 'center', position: 'relative', zIndex: 1 }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: '8px',
              padding: '8px 18px', background: colors.glass,
              backdropFilter: 'blur(20px)',
              border: `1px solid ${colors.border}`,
              borderRadius: '100px',
              fontSize: '0.875rem', fontWeight: '500',
              color: colors.primary, marginBottom: '24px',
            }}
          >
            <Heart size={14} />
            <span>For Earth and Humanity</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            style={{
              fontSize: isMobile ? '2.25rem' : '3.5rem',
              fontWeight: '800', lineHeight: 1.1,
              marginBottom: '24px', letterSpacing: '-0.02em',
            }}
          >
            <span style={{ color: colors.text }}>{t('mission_title').split(' ').slice(0, -1).join(' ')}</span>
            <br />
            <span className="love-gradient-text">{t('mission_title').split(' ').slice(-1)[0]}</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            style={{
              fontSize: isMobile ? '1.1rem' : '1.3rem',
              color: colors.textMuted, maxWidth: '700px',
              margin: '0 auto', lineHeight: 1.6,
            }}
          >
            {t('mission_subtitle')}
          </motion.p>
        </div>
      </section>

      {/* Global Crisis Stats */}
      <section style={{ padding: isMobile ? '60px 20px' : '80px 48px', background: colors.bg }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            style={{ textAlign: 'center', marginBottom: '48px' }}
          >
            <div style={{
              display: 'inline-block',
              padding: '6px 16px',
              background: `${colors.primary}15`,
              color: colors.primary,
              borderRadius: '100px',
              fontSize: '0.875rem', fontWeight: '600',
              marginBottom: '16px',
            }}>
              🌍 The Global Challenge
            </div>
            <h2 style={{ fontSize: isMobile ? '1.75rem' : '2.5rem', fontWeight: '800', color: colors.text, marginBottom: '16px' }}>
              Our Planet at a Crossroads
            </h2>
            <p style={{ fontSize: '1.1rem', color: colors.textMuted, maxWidth: '700px', margin: '0 auto' }}>
              The crisis of natural resources is a global phenomenon. These are the numbers that define our urgency.
            </p>
          </motion.div>

          <motion.div
            variants={container}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            style={{
              display: 'grid',
              gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(240px, 1fr))',
              gap: '20px',
            }}
          >
            {globalStats.map((stat) => {
              const Icon = stat.icon;
              return (
                <motion.div
                  key={stat.key}
                  variants={item}
                  whileHover={{ y: -8 }}
                  style={{
                    background: colors.cardBg,
                    backdropFilter: 'blur(20px)',
                    border: `1px solid ${colors.border}`,
                    padding: '28px',
                    borderRadius: '20px',
                    position: 'relative',
                    overflow: 'hidden',
                  }}
                >
                  <div style={{
                    position: 'absolute', top: '-20px', right: '-20px',
                    width: '100px', height: '100px',
                    background: `radial-gradient(circle, ${stat.color}30, transparent 70%)`,
                    borderRadius: '50%',
                  }} />
                  <div style={{
                    width: '56px', height: '56px',
                    borderRadius: '14px',
                    background: `${stat.color}20`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    marginBottom: '16px',
                    border: `2px solid ${stat.color}30`,
                  }}>
                    <Icon size={28} color={stat.color} strokeWidth={2.5} />
                  </div>
                  <div style={{ fontSize: '2.5rem', fontWeight: '800', color: stat.color, lineHeight: 1, marginBottom: '8px' }}>
                    {stat.value}
                  </div>
                  <div style={{ fontSize: '0.95rem', color: colors.text, marginBottom: '8px', lineHeight: 1.5 }}>
                    {t(stat.key)}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: colors.textMuted, fontStyle: 'italic' }}>
                    Source: {stat.source}
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        </div>
      </section>

      {/* Paradigm Shift */}
      <section style={{
        padding: isMobile ? '60px 20px' : '80px 48px',
        background: theme === 'dark'
          ? 'linear-gradient(180deg, #0c0a09 0%, #1c1917 100%)'
          : 'linear-gradient(180deg, #fef3c7 0%, #fffbeb 100%)',
      }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            style={{
              background: colors.cardBg,
              backdropFilter: 'blur(20px)',
              border: `1px solid ${colors.border}`,
              padding: isMobile ? '32px 24px' : '48px',
              borderRadius: '24px',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <div style={{
              position: 'absolute', top: 0, left: 0, right: 0, height: '4px',
              background: `linear-gradient(90deg, ${colors.primary}, ${colors.accent})`,
            }} />

            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
              <div style={{
                width: '56px', height: '56px', borderRadius: '14px',
                background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
              }}>
                <Target size={28} color="white" strokeWidth={2.5} />
              </div>
              <div>
                <h2 style={{ fontSize: '1.75rem', fontWeight: '800', color: colors.text, margin: 0 }}>
                  A Paradigm Shift
                </h2>
                <p style={{ color: colors.textMuted, margin: '4px 0 0' }}>
                  From siloed management to Integrated Landscape Management (ILM)
                </p>
              </div>
            </div>

            <p style={{ color: colors.text, lineHeight: 1.8, marginBottom: '20px', fontSize: '1.05rem' }}>
              Decades of managing water, soil, and livelihoods in silos—with a focus on
              supply-side infrastructure (dams, deep wells, horizontal expansion)—has led
              to a <strong>paradigm failure</strong>. The crisis is not simply a shortage of
              physical resources; it is the failure of a worldview that sees land as a
              collection of separate parts rather than a living, interconnected system.
            </p>

            <p style={{ color: colors.text, lineHeight: 1.8, fontSize: '1.05rem' }}>
              <strong style={{ color: colors.primary }}>Hydroma Nojin</strong> is an
              operational, evidence-based response. We transition from scattered
              project-based management to <strong>Integrated Landscape Management (ILM)</strong>,
              where the landscape is the primary unit of decision-making. In this view, water,
              soil, vegetation, livelihoods, and governance are intertwined layers of one system.
              An intervention upstream (e.g., rangeland restoration) directly affects downstream
              variables (aquifer recharge, livelihood stability).
            </p>
          </motion.div>
        </div>
      </section>

      {/* Six Approaches */}
      <section style={{ padding: isMobile ? '60px 20px' : '80px 48px', background: colors.bg }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            style={{ textAlign: 'center', marginBottom: '48px' }}
          >
            <div style={{
              display: 'inline-block',
              padding: '6px 16px',
              background: `${colors.accent}15`,
              color: colors.accent,
              borderRadius: '100px',
              fontSize: '0.875rem', fontWeight: '600',
              marginBottom: '16px',
            }}>
              🌐 Six Global Approaches
            </div>
            <h2 style={{ fontSize: isMobile ? '1.75rem' : '2.5rem', fontWeight: '800', color: colors.text, marginBottom: '16px' }}>
              The Hydroma Architecture
            </h2>
            <p style={{ fontSize: '1.1rem', color: colors.textMuted, maxWidth: '700px', margin: '0 auto' }}>
              Six internationally recognized approaches, integrated into a native architecture
              adapted to diverse ecosystems worldwide.
            </p>
          </motion.div>

          <motion.div
            variants={container}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            style={{
              display: 'grid',
              gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '20px',
            }}
          >
            {sixApproaches.map((app, i) => {
              const Icon = app.icon;
              return (
                <motion.div
                  key={i}
                  variants={item}
                  whileHover={{ y: -6 }}
                  style={{
                    background: colors.cardBg,
                    backdropFilter: 'blur(20px)',
                    border: `1px solid ${colors.border}`,
                    padding: '28px',
                    borderRadius: '20px',
                    position: 'relative',
                    overflow: 'hidden',
                  }}
                >
                  <div style={{
                    position: 'absolute', top: '-30px', right: '-30px',
                    width: '120px', height: '120px',
                    background: `radial-gradient(circle, ${app.color}25, transparent 70%)`,
                    borderRadius: '50%',
                  }} />
                  <div style={{
                    width: '52px', height: '52px',
                    borderRadius: '14px',
                    background: `${app.color}20`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    marginBottom: '16px',
                    border: `2px solid ${app.color}30`,
                    position: 'relative', zIndex: 1,
                  }}>
                    <Icon size={26} color={app.color} strokeWidth={2.5} />
                  </div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: '700', color: colors.text, marginBottom: '10px', position: 'relative', zIndex: 1 }}>
                    {getLocalized(app.title)}
                  </h3>
                  <p style={{ color: colors.textMuted, fontSize: '0.9rem', lineHeight: 1.7, position: 'relative', zIndex: 1 }}>
                    {getLocalized(app.desc)}
                  </p>
                </motion.div>
              );
            })}
          </motion.div>
        </div>
      </section>

      {/* Three-Layered Message */}
      <section style={{
        padding: isMobile ? '60px 20px' : '80px 48px',
        background: theme === 'dark'
          ? 'linear-gradient(180deg, #1c1917 0%, #0c0a09 100%)'
          : 'linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%)',
      }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            style={{ textAlign: 'center', marginBottom: '48px' }}
          >
            <div style={{
              display: 'inline-block',
              padding: '6px 16px',
              background: `${colors.warm}25`,
              color: colors.primaryDark,
              borderRadius: '100px',
              fontSize: '0.875rem', fontWeight: '600',
              marginBottom: '16px',
            }}>
              💛 Three-Layered Message
            </div>
            <h2 style={{ fontSize: isMobile ? '1.75rem' : '2.5rem', fontWeight: '800', color: colors.text, marginBottom: '16px' }}>
              Our Message to the World
            </h2>
          </motion.div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {threeMessages.map((msg, i) => {
              const Icon = msg.icon;
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: i % 2 === 0 ? -30 : 30 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  style={{
                    background: colors.cardBg,
                    backdropFilter: 'blur(20px)',
                    border: `1px solid ${colors.border}`,
                    borderRadius: '24px',
                    overflow: 'hidden',
                  }}
                >
                  <div style={{
                    padding: isMobile ? '20px' : '24px 32px',
                    background: `linear-gradient(90deg, ${msg.color}15, transparent)`,
                    borderBottom: `1px solid ${colors.border}`,
                    display: 'flex', alignItems: 'center', gap: '16px',
                  }}>
                    <div style={{
                      width: '52px', height: '52px', borderRadius: '14px',
                      background: msg.color,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      flexShrink: 0,
                      boxShadow: `0 4px 16px ${msg.color}40`,
                    }}>
                      <Icon size={26} color="white" strokeWidth={2.5} />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '1.25rem', fontWeight: '700', color: colors.text, margin: 0 }}>
                        {getLocalized(msg.audience)}
                      </h3>
                      <p style={{ color: msg.color, fontSize: '0.9rem', margin: '4px 0 0', fontWeight: '500' }}>
                        {getLocalized(msg.subtitle)}
                      </p>
                    </div>
                  </div>
                  <div style={{ padding: isMobile ? '24px' : '32px' }}>
                    <p style={{ color: colors.text, lineHeight: 1.8, fontSize: '1rem', margin: 0 }}>
                      {getLocalized(msg.text)}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Philosophy Quote */}
      <section style={{
        padding: isMobile ? '60px 20px' : '100px 48px',
        background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.accent} 100%)`,
        position: 'relative',
        overflow: 'hidden',
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
        <div style={{ maxWidth: '900px', margin: '0 auto', textAlign: 'center', position: 'relative', zIndex: 1, color: 'white' }}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
          >
            <Sparkles size={48} style={{ marginBottom: '24px', opacity: 0.9 }} />
            <h2 style={{ fontSize: isMobile ? '1.75rem' : '2.5rem', fontWeight: '800', marginBottom: '24px', lineHeight: 1.3 }}>
              {t('home_philosophy_title')}
            </h2>
            <p style={{ fontSize: '1.15rem', lineHeight: 1.8, opacity: 0.95, fontStyle: 'italic' }}>
              "{t('home_philosophy_text')}"
            </p>
          </motion.div>
        </div>
      </section>

      {/* CTA to Donate */}
      <section style={{ padding: isMobile ? '60px 20px' : '80px 48px', background: colors.bg }}>
        <div style={{ maxWidth: '900px', margin: '0 auto', textAlign: 'center' }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <Heart size={56} color={colors.primary} style={{ marginBottom: '20px' }} className="animate-heartbeat" />
            <h2 style={{ fontSize: isMobile ? '1.75rem' : '2.25rem', fontWeight: '800', color: colors.text, marginBottom: '16px' }}>
              Join the Restoration
            </h2>
            <p style={{ fontSize: '1.15rem', color: colors.textMuted, marginBottom: '32px', lineHeight: 1.7 }}>
              Every contribution restores water, soil, and hope. Whether you are a scientist,
              a policymaker, a philanthropist, or a citizen of the world—there is a place for
              you in this movement.
            </p>
            <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', flexWrap: 'wrap' }}>
              <a href="/donate">
                <motion.button
                  whileHover={{ scale: 1.05, boxShadow: `0 16px 40px ${colors.primary}40` }}
                  whileTap={{ scale: 0.98 }}
                  style={{
                    padding: '14px 32px',
                    background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
                    color: 'white', border: 'none', borderRadius: '12px',
                    fontSize: '1rem', fontWeight: '600',
                    display: 'flex', alignItems: 'center', gap: '8px',
                    cursor: 'pointer',
                  }}
                >
                  <Heart size={18} />
                  Support Our Mission
                  <ArrowRight size={18} />
                </motion.button>
              </a>
              <a href="/contact">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.98 }}
                  style={{
                    padding: '14px 32px',
                    background: 'transparent',
                    color: colors.primary,
                    border: `2px solid ${colors.primary}`,
                    borderRadius: '12px',
                    fontSize: '1rem', fontWeight: '600',
                    cursor: 'pointer',
                  }}
                >
                  Partner With Us
                </motion.button>
              </a>
            </div>
          </motion.div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
