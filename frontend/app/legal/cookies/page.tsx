'use client';
import Footer from '../../../components/layout/Footer';
import { useI18n } from '../../../lib/i18n-context';
import { useTheme } from '../../../lib/theme-context';
import { motion } from 'framer-motion';
import { Cookie } from 'lucide-react';

export default function Cookies_Page() {
  const { t, direction } = useI18n();
  const { colors } = useTheme();

  return (
    <div dir={direction} style={{ background: colors.bg, minHeight: '100vh' }}>
      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '60px 32px' }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.accent} 100%)`,
            padding: '48px 40px',
            borderRadius: '20px',
            color: 'white',
            marginBottom: '40px',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 30, repeat: Infinity, ease: 'linear' }}
            style={{
              position: 'absolute', top: '-40px', right: '-40px',
              width: '160px', height: '160px',
              background: 'radial-gradient(circle, rgba(255,255,255,0.15), transparent 70%)',
              borderRadius: '50%',
            }}
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', position: 'relative', zIndex: 1 }}>
            <Cookie size={40} strokeWidth={2} />
            <div>
              <h1 style={{ fontSize: '2rem', fontWeight: '800', margin: 0 }}>
                Cookie Policy
              </h1>
              <p style={{ margin: '8px 0 0', opacity: 0.9 }}>
                Last updated: August 2026
              </p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          style={{
            background: colors.cardBg,
            backdropFilter: 'blur(20px)',
            border: `1px solid ${colors.border}`,
            padding: '40px',
            borderRadius: '20px',
            lineHeight: 1.8,
          }}
        >
          
          <section style={{ marginBottom: '32px' }}>
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>1. What Are Cookies?</h2>
            <p style={{ color: colors.text }}>
              Cookies are small text files that help us remember your preferences (language,
              theme) and improve your experience. We use <strong>only essential and functional
              cookies</strong>—never advertising or tracking cookies.
            </p>
          </section>

          <section style={{ marginBottom: '32px' }}>
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>2. Cookies We Use</h2>
            <table style={{ width: '100%', borderCollapse: 'collapse', color: colors.text }}>
              <thead>
                <tr style={{ borderBottom: `2px solid ${colors.border}` }}>
                  <th style={{ padding: '12px', textAlign: 'start' }}>Cookie</th>
                  <th style={{ padding: '12px', textAlign: 'start' }}>Purpose</th>
                  <th style={{ padding: '12px', textAlign: 'start' }}>Duration</th>
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: `1px solid ${colors.border}` }}>
                  <td style={{ padding: '12px' }}>locale</td>
                  <td style={{ padding: '12px' }}>Remember your language</td>
                  <td style={{ padding: '12px' }}>1 year</td>
                </tr>
                <tr style={{ borderBottom: `1px solid ${colors.border}` }}>
                  <td style={{ padding: '12px' }}>theme</td>
                  <td style={{ padding: '12px' }}>Remember light/dark mode</td>
                  <td style={{ padding: '12px' }}>1 year</td>
                </tr>
                <tr>
                  <td style={{ padding: '12px' }}>session</td>
                  <td style={{ padding: '12px' }}>Keep you logged in</td>
                  <td style={{ padding: '12px' }}>7 days</td>
                </tr>
              </tbody>
            </table>
          </section>

          <section style={{ marginBottom: '32px' }}>
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>3. Third-Party Services</h2>
            <p style={{ color: colors.text }}>
              We use privacy-respecting services:
            </p>
            <ul style={{ color: colors.text, paddingLeft: '24px' }}>
              <li><strong>Google Fonts:</strong> for beautiful typography (no tracking)</li>
              <li><strong>Sentinel Hub:</strong> satellite imagery (public data)</li>
              <li><strong>Polygon blockchain:</strong> for ECO tokens (transparent, public)</li>
            </ul>
          </section>

          <section>
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>4. Your Control</h2>
            <p style={{ color: colors.text }}>
              You can disable cookies in your browser settings. Essential cookies may be required
              for login and language preferences. Clear your browser data anytime to reset.
            </p>
          </section>

        </motion.div>
      </div>
      <Footer />
    </div>
  );
}
