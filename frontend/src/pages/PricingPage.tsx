import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Check, Zap, Crown, Infinity, Wallet, Sparkles } from 'lucide-react';
import { PublicLayout } from '../components/layout/PublicLayout';
import { CryptoPaymentModal } from '../components/payment/CryptoPaymentModal';
import { SUBSCRIPTION_PLANS, type SubscriptionPlan } from '../config/crypto';

const planIcons: Record<string, React.ReactNode> = {
  starter: <Zap size={24} />,
  farmer: <Sparkles size={24} />,
  enterprise: <Crown size={24} />,
  lifetime: <Infinity size={24} /> };

export const PricingPage: React.FC = () => {
  const [paymentModalOpen, setPaymentModalOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<SubscriptionPlan | null>(null);

  const handlePlanSelect = (plan: SubscriptionPlan) => {
    setSelectedPlan(plan);
    setPaymentModalOpen(true);
  };

  return (
    <PublicLayout>
      <section
        style={{
          padding: '6rem 2rem',
          minHeight: '100vh',
          background: 'linear-gradient(180deg, var(--color-bg) 0%, var(--color-surface) 100%)' }}
      >
        <div style={{ maxWidth: 1400, margin: '0 auto' }}>
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ textAlign: 'center', marginBottom: '4rem' }}
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', delay: 0.2 }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 1rem',
                background: 'var(--color-primary)',
                color: 'white',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.875rem',
                fontWeight: 600,
                marginBottom: '1.5rem' }}
            >
              <Wallet size={16} />
              پرداخت فقط با رمزارز
            </motion.div>
            <h1 style={{ fontSize: 'clamp(2rem, 5vw, 3rem)', fontWeight: 700, marginBottom: '1rem' }}>
              پلنی را انتخاب کنید که برای شما مناسب است
            </h1>
            <p style={{ fontSize: '1.125rem', color: 'var(--color-text-secondary)', maxWidth: 600, margin: '0 auto' }}>
              تمام پلن‌ها شامل ۳۰ روز ضمانت بازگشت وجه هستند. بدون قرارداد، بدون هزینه پنهان.
            </p>
          </motion.div>

          {/* Plans Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '2rem',
              marginBottom: '4rem' }}
          >
            {SUBSCRIPTION_PLANS.map((plan, index) => (
              <motion.div
                key={plan.id}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ y: -8, scale: 1.02 }}
                className="card"
                style={{
                  position: 'relative',
                  padding: '2rem',
                  border: plan.recommended
                    ? `2px solid ${plan.color}`
                    : '1px solid var(--color-border)',
                  boxShadow: plan.recommended ? `0 20px 40px ${plan.color}30` : 'none' }}
              >
                {plan.recommended && (
                  <div
                    style={{
                      position: 'absolute',
                      top: -12,
                      left: '50%',
                      transform: 'translateX(-50%)',
                      background: plan.color,
                      color: 'white',
                      padding: '0.25rem 1rem',
                      borderRadius: 'var(--radius-full)',
                      fontSize: '0.75rem',
                      fontWeight: 700 }}
                  >
                    محبوب‌ترین
                  </div>
                )}

                {/* Plan Icon */}
                <div
                  style={{
                    width: 56,
                    height: 56,
                    borderRadius: 'var(--radius-xl)',
                    background: `${plan.color}20`,
                    color: plan.color,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: '1rem' }}
                >
                  {planIcons[plan.id]}
                </div>

                {/* Plan Name */}
                <h3 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.25rem' }}>
                  {plan.nameFa}
                </h3>
                <p style={{ color: 'var(--color-text-tertiary)', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
                  {plan.name}
                </p>

                {/* Price */}
                <div style={{ marginBottom: '1.5rem' }}>
                  <span style={{ fontSize: '3rem', fontWeight: 800, color: 'var(--color-text-primary)' }}>
                    ${plan.priceUsd}
                  </span>
                  <span style={{ color: 'var(--color-text-tertiary)', marginLeft: '0.25rem' }}>
                    /{plan.period === 'monthly' ? 'ماه' : plan.period === 'yearly' ? 'سال' : 'مادام‌العمر'}
                  </span>
                </div>

                {/* Features */}
                <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 2rem 0' }}>
                  {plan.features.map((feature, i) => (
                    <li
                      key={i}
                      style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '0.5rem',
                        padding: '0.5rem 0',
                        fontSize: '0.875rem',
                        color: 'var(--color-text-secondary)' }}
                    >
                      <Check size={16} color={plan.color} style={{ flexShrink: 0, marginTop: '2px' }} />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>

                {/* CTA Button */}
                <motion.button
                  onClick={() => handlePlanSelect(plan)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="btn"
                  style={{
                    width: '100%',
                    padding: '0.875rem',
                    background: plan.recommended ? plan.color : 'var(--color-surface)',
                    color: plan.recommended ? 'white' : 'var(--color-text-primary)',
                    border: plan.recommended ? 'none' : '1px solid var(--color-border)',
                    fontWeight: 600 }}
                >
                  <Wallet size={16} />
                  پرداخت و شروع
                </motion.button>
              </motion.div>
            ))}
          </div>

          {/* FAQ / Trust Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            style={{
              maxWidth: 900,
              margin: '0 auto',
              padding: '3rem',
              background: 'var(--color-surface)',
              borderRadius: 'var(--radius-2xl)',
              border: '1px solid var(--color-border)' }}
          >
            <h3 style={{ textAlign: 'center', fontSize: '1.5rem', fontWeight: 700, marginBottom: '2rem' }}>
              سوالات متداول
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
              {[
                {
                  q: 'چگونه پرداخت کنم؟',
                  a: 'روی پلن مورد نظر کلیک کنید، شبکه مورد علاقه خود را انتخاب کنید و آدرس کیف پول را کپی کنید یا مستقیماً با MetaMask پرداخت کنید.' },
                {
                  q: 'کدام رمزارزها پذیرفته می‌شوند؟',
                  a: 'USDT (Tether) در چهار شبکه TRC20، ERC20، BEP20 و Polygon پذیرفته می‌شود.' },
                {
                  q: 'اشتراک چقدر طول می‌کشد تا فعال شود؟',
                  a: 'پس از تأیید تراکنش روی بلاکچین (معمولاً چند دقیقه)، اشتراک شما به‌صورت خودکار فعال می‌شود.' },
                {
                  q: 'آیا ضمانت بازگشت وجه دارید؟',
                  a: 'بله، تا ۳۰ روز پس از خرید می‌توانید درخواست بازگشت وجه دهید.' },
              ].map((item, i) => (
                <div key={i}>
                  <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                    {item.q}
                  </h4>
                  <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem', lineHeight: 1.7, margin: 0 }}>
                    {item.a}
                  </p>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Payment Modal */}
      {selectedPlan && (
        <CryptoPaymentModal
          isOpen={paymentModalOpen}
          onClose={() => setPaymentModalOpen(false)}
          amountUsd={selectedPlan.priceUsd}
          planName={selectedPlan.nameFa}
          onSuccess={(txHash, network) => {
            console.log('Payment successful:', { txHash, network });
            // TODO: اینجا می‌توان به backend اطلاع داد
          }}
        />
      )}
    </PublicLayout>
  );
};
