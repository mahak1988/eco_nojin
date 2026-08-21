'use client';
import Footer from '../../../components/layout/Footer';
import { useI18n } from '../../../lib/i18n-context';
import { useTheme } from '../../../lib/theme-context';
import { motion } from 'framer-motion';
import { FileText } from 'lucide-react';

export default function Terms_Page() {
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
            <FileText size={40} strokeWidth={2} />
            <div>
              <h1 style={{ fontSize: '2rem', fontWeight: '800', margin: 0 }}>
                Terms of Service
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
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>1. Our Shared Mission</h2>
            <p style={{ color: colors.text }}>
              By using Hydroma Nojin, you join a global community working to restore degraded
              lands, empower smallholder farmers, and build climate resilience. These terms reflect
              our values of <strong>transparency, equity, and mutual respect</strong>.
            </p>
          </section>

          <section style={{ marginBottom: '32px' }}>
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>2. Your Responsibilities</h2>
            <ul style={{ color: colors.text, paddingLeft: '24px' }}>
              <li>Provide accurate information for fair service delivery</li>
              <li>Use the platform for lawful purposes aligned with our mission</li>
              <li>Respect other community members and their data</li>
              <li>Report scientific data honestly (especially for carbon credits)</li>
            </ul>
          </section>

          <section style={{ marginBottom: '32px' }}>
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>3. Our Commitments to You</h2>
            <ul style={{ color: colors.text, paddingLeft: '24px' }}>
              <li>Provide free basic access to all farmers (tier 1 always free)</li>
              <li>Share scientific methodologies transparently</li>
              <li>Protect your privacy (see Privacy Policy)</li>
              <li>Operate with humanitarian principles</li>
              <li>Compensate carbon sequestration fairly</li>
            </ul>
          </section>

          <section style={{ marginBottom: '32px' }}>
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>4. Scientific Advice Disclaimer</h2>
            <p style={{ color: colors.text }}>
              Our recommendations are based on peer-reviewed science (FAO, IPCC, CMIP6) and
              satellite data, but agriculture involves inherent uncertainty. Always combine our
              advice with local knowledge and professional consultation.
            </p>
          </section>

          <section style={{ marginBottom: '32px' }}>
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>5. Carbon Credits and Blockchain</h2>
            <p style={{ color: colors.text }}>
              ECO tokens represent verified carbon sequestration and are utility tokens, not
              securities. They are redeemable for platform services. Trading on external exchanges
              may be restricted in your jurisdiction.
            </p>
          </section>

          <section>
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>6. Fair Use and Community Values</h2>
            <p style={{ color: colors.text }}>
              We reserve the right to suspend accounts that harm our mission, exploit vulnerable
              users, or provide fraudulent data. We believe in restorative practices over
              punitive ones whenever possible.
            </p>
          </section>

        </motion.div>
      </div>
      <Footer />
    </div>
  );
}
