'use client';
import Navbar from '../../../components/layout/Navbar';
import Footer from '../../../components/layout/Footer';
import { useI18n } from '../../../lib/i18n-context';
import { useTheme } from '../../../lib/theme-context';
import { motion } from 'framer-motion';
import { Shield } from 'lucide-react';

export default function Privacy_Page() {
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
            <Shield size={40} strokeWidth={2} />
            <div>
              <h1 style={{ fontSize: '2rem', fontWeight: '800', margin: 0 }}>
                Privacy Policy
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
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>1. Our Commitment to Privacy</h2>
            <p style={{ color: colors.text }}>
              Hydroma Nojin is a humanitarian platform dedicated to restoring ecosystems and
              empowering rural communities worldwide. We believe that <strong>privacy is a
              fundamental human right</strong>, especially for smallholder farmers, pastoralists,
              and indigenous communities who entrust us with their land, knowledge, and livelihoods.
            </p>
          </section>

          <section style={{ marginBottom: '32px' }}>
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>2. Data We Collect</h2>
            <p style={{ color: colors.text }}>We only collect data essential to our mission:</p>
            <ul style={{ color: colors.text, paddingLeft: '24px' }}>
              <li><strong>Account data:</strong> name, email, preferred language, region</li>
              <li><strong>Farm data:</strong> coordinates (optional), soil measurements, crop choices</li>
              <li><strong>Usage data:</strong> module interactions to improve our scientific models</li>
              <li><strong>Communication:</strong> messages you send us</li>
            </ul>
            <p style={{ color: colors.text, marginTop: '16px' }}>
              We <strong>never</strong> sell your data. We <strong>never</strong> use your data for advertising.
            </p>
          </section>

          <section style={{ marginBottom: '32px' }}>
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>3. How We Use Your Data</h2>
            <p style={{ color: colors.text }}>Your data helps us:</p>
            <ul style={{ color: colors.text, paddingLeft: '24px' }}>
              <li>Provide personalized agricultural recommendations</li>
              <li>Verify carbon sequestration for fair compensation</li>
              <li>Connect you with markets, cooperatives, and support</li>
              <li>Improve our scientific models (anonymized and aggregated)</li>
              <li>Report impact to humanitarian partners (anonymized)</li>
            </ul>
          </section>

          <section style={{ marginBottom: '32px' }}>
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>4. Your Rights (GDPR, CCPA)</h2>
            <p style={{ color: colors.text }}>You have the right to:</p>
            <ul style={{ color: colors.text, paddingLeft: '24px' }}>
              <li>Access all data we hold about you</li>
              <li>Correct inaccurate data</li>
              <li>Delete your account and all associated data</li>
              <li>Export your data in portable format</li>
              <li>Object to processing and withdraw consent</li>
            </ul>
            <p style={{ color: colors.text, marginTop: '16px' }}>
              Contact us at <strong>privacy@hydroma-nojin.org</strong> to exercise any right.
            </p>
          </section>

          <section style={{ marginBottom: '32px' }}>
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>5. Data Security</h2>
            <p style={{ color: colors.text }}>
              We use end-to-end encryption, blockchain-backed integrity checks for carbon data,
              and follow industry best practices. However, no system is perfectly secure, and
              we are transparent about any incidents.
            </p>
          </section>

          <section>
            <h2 style={{ color: colors.primary, marginBottom: '16px', fontSize: '1.4rem' }}>6. Children and Vulnerable Communities</h2>
            <p style={{ color: colors.text }}>
              We take extra care when working with children, indigenous communities, and vulnerable
              populations. We comply with COPPA and seek informed consent with community leaders
              when appropriate.
            </p>
          </section>

        </motion.div>
      </div>
      <Footer />
    </div>
  );
}
