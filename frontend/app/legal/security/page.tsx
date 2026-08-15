'use client';
import Navbar from '../../../components/layout/Navbar';
import Footer from '../../../components/layout/Footer';
import { useI18n } from '../../../lib/i18n-context';
import { useTheme } from '../../../lib/theme-context';
import { motion } from 'framer-motion';
import { Lock } from 'lucide-react';

export default function Security_Page() {
  const { t, direction } = useI18n();
  const { colors } = useTheme();

  return (
    <div dir={direction} style={{ background: colors.bg, minHeight: '100vh' }}>
      <Navbar />
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
            <Lock size={40} strokeWidth={2} />
            <div>
              <h1 style={{ fontSize: '2rem', fontWeight: '800', margin: 0 }}>
                Security Policy
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
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>1. Our Security Philosophy</h2>
            <p style={{ color: colors.text }}>
              We protect our users—many of whom are vulnerable smallholder farmers—with the
              same rigor as financial institutions. Security is not a feature; it is a
              <strong> human rights commitment</strong>.
            </p>
          </section>

          <section style={{ marginBottom: '32px' }}>
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>2. Technical Measures</h2>
            <ul style={{ color: colors.text, paddingLeft: '24px' }}>
              <li>End-to-end encryption for sensitive data</li>
              <li>HTTPS everywhere (TLS 1.3)</li>
              <li>Blockchain integrity for carbon data (immutable audit trail)</li>
              <li>Regular security audits by third parties</li>
              <li>Bug bounty program for responsible disclosure</li>
              <li>Offline-first design (works without internet)</li>
            </ul>
          </section>

          <section style={{ marginBottom: '32px' }}>
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>3. Responsible Disclosure</h2>
            <p style={{ color: colors.text }}>
              If you find a security vulnerability, please report it to
              <strong> security@hydroma-nojin.org</strong>. We commit to:
            </p>
            <ul style={{ color: colors.text, paddingLeft: '24px' }}>
              <li>Acknowledge within 48 hours</li>
              <li>Investigate and triage within 7 days</li>
              <li>Fix critical issues within 30 days</li>
              <li>Credit researchers (if desired) after fix</li>
              <li>Never pursue legal action for good-faith research</li>
            </ul>
          </section>

          <section style={{ marginBottom: '32px' }}>
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>4. Incident Response</h2>
            <p style={{ color: colors.text }}>
              In the event of a data breach, we will notify affected users within 72 hours
              (GDPR requirement) with clear, non-technical explanations and steps to protect
              themselves. We will also publish a public incident report.
            </p>
          </section>

          <section>
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>5. User Security Tips</h2>
            <ul style={{ color: colors.text, paddingLeft: '24px' }}>
              <li>Use strong, unique passwords</li>
              <li>Enable two-factor authentication when available</li>
              <li>Never share your credentials</li>
              <li>Report suspicious messages to us</li>
            </ul>
          </section>

        </motion.div>
      </div>
      <Footer />
    </div>
  );
}
