"use client";
import { useState, useEffect } from 'react';
import Footer from '../../../components/layout/Footer';
import { useI18n } from '../../../lib/i18n-context';
import { useTheme } from '../../../lib/theme-context';
import { useAuth } from '../../../lib/auth-context';
import { api } from '../../../lib/api-client';
import { motion } from 'framer-motion';
import {
  Wallet, TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight,
  ShoppingBag, Award, Gift, Zap, Star, TreePine, Satellite,
  FlaskConical, Users, BookOpen, CheckCircle2
} from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area
} from 'recharts';

export default function EcoWalletPage() {
  const { t, direction, locale: language } = useI18n();
  const { colors } = useTheme();
  const { isAuthenticated } = useAuth();
  const currentLang = t('ew_en');

  const [wallet, setWallet] = useState<any>(null);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [earningOptions, setEarningOptions] = useState<any[]>([]);
  const [redemptionOptions, setRedemptionOptions] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionMessage, setActionMessage] = useState<{type: 'success'|'error', text: string} | null>(null);

  useEffect(() => {
    if (isAuthenticated) loadAll();
    else setLoading(false);
  }, [isAuthenticated]);

  const loadAll = async () => {
    setLoading(true);
    const [w, t, eo, ro, s] = await Promise.all([
      api.get<any>('/api/v1/ecowallet/wallet'),
      api.get<any>('/api/v1/ecowallet/transactions?limit=20'),
      api.get<any>('/api/v1/ecowallet/earning-options'),
      api.get<any>('/api/v1/ecowallet/redemption-options'),
      api.get<any>('/api/v1/ecowallet/stats'),
    ]);
    if (w.success && w.data) setWallet(w.data);
    if (t.success && t.data) setTransactions(t.data);
    if (eo.success && eo.data) setEarningOptions(eo.data.options);
    if (ro.success && ro.data) setRedemptionOptions(ro.data.options);
    if (s.success && s.data) setStats(s.data);
    setLoading(false);
  };

  const earn = async (category: string) => {
    const res = await api.post<any>('/api/v1/ecowallet/earn', { category, quantity: 1 });
    if (res.success) {
      setActionMessage({ type: 'success', text: `+${res.data.amount_earned} ECO earned!` });
      await loadAll();
    } else {
      setActionMessage({ type: 'error', text: res.error || 'Failed to earn' });
    }
    setTimeout(() => setActionMessage(null), 3000);
  };

  const redeem = async (category: string) => {
    const res = await api.post<any>('/api/v1/ecowallet/redeem', { category });
    if (res.success) {
      setActionMessage({ type: 'success', text: `Redeemed: ${res.data.service_received}` });
      await loadAll();
    } else {
      setActionMessage({ type: 'error', text: res.error || 'Failed to redeem' });
    }
    setTimeout(() => setActionMessage(null), 3000);
  };

  if (!isAuthenticated) {
    return (
      <div dir={direction} style={{ background: colors.bg, minHeight: '100vh' }}>
        <div style={{ maxWidth: '800px', margin: '0 auto', padding: '80px 20px', textAlign: 'center' }}>
          <Wallet size={64} color={colors.textMuted} style={{ marginBottom: '16px', opacity: 0.3 }} />
          <h2 style={{ color: colors.text, marginBottom: '8px' }}>
            {t('ew_please_login')}
          </h2>
          <p style={{ color: colors.textMuted }}>
            {t('ew_login_to_access_your_eco_wallet')}
          </p>
        </div>
        <Footer />
      </div>
    );
  }

  if (loading) {
    return (
      <div dir={direction} style={{ background: colors.bg, minHeight: '100vh' }}>
        <div style={{ padding: '80px 20px', textAlign: 'center', color: colors.textMuted }}>
          Loading wallet...
        </div>
        <Footer />
      </div>
    );
  }

  const COLORS = ['#10b981', '#f59e0b', '#3b82f6', '#8b5cf6', '#ec4899', '#06b6d4', '#ef4444'];

  return (
    <div dir={direction} style={{ background: colors.bg, minHeight: '100vh' }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '32px 20px' }}>
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{
            background: `linear-gradient(135deg, #8b5cf6, #ec4899, #f59e0b)`,
            padding: '40px', borderRadius: '24px', color: 'white',
            marginBottom: '32px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <Wallet size={40} />
            <div>
              <h1 style={{ fontSize: '2rem', fontWeight: '800', margin: 0 }}>
                {t('ew_eco_wallet')}
              </h1>
              <p style={{ margin: '4px 0 0', opacity: 0.95 }}>
                {t('ew_sustainable_economy_for_farmers')}
              </p>
            </div>
          </div>
        </motion.div>

        {/* Action Message */}
        {actionMessage && (
          <motion.div
            initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            style={{
              padding: '14px 20px', marginBottom: '20px',
              background: actionMessage.type === 'success' ? `${colors.success}15` : `${colors.danger}15`,
              border: `1px solid ${actionMessage.type === 'success' ? colors.success : colors.danger}40`,
              borderRadius: '12px',
              color: actionMessage.type === 'success' ? colors.success : colors.danger,
              fontSize: '0.95rem', fontWeight: '600',
            }}
          >
            {actionMessage.type === 'success' ? '✅' : '❌'} {actionMessage.text}
          </motion.div>
        )}

        {/* Balance Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{
            background: colors.cardBg, padding: '32px', borderRadius: '20px',
            border: `1px solid ${colors.border}`, marginBottom: '24px',
            display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px',
          }}
        >
          <div>
            <div style={{ fontSize: '0.85rem', color: colors.textMuted, marginBottom: '8px' }}>
              {t('ew_current_balance')}
            </div>
            <div style={{ fontSize: '2.5rem', fontWeight: '800', color: colors.primary, display: 'flex', alignItems: 'baseline', gap: '8px' }}>
              {wallet?.balance.toFixed(2)}
              <span style={{ fontSize: '1rem', color: colors.textMuted }}>ECO</span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.85rem', color: colors.textMuted, marginBottom: '8px' }}>
              {t('ew_total_earned')}
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: '700', color: colors.success, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ArrowUpRight size={20} />
              {wallet?.total_earned.toFixed(0)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.85rem', color: colors.textMuted, marginBottom: '8px' }}>
              {t('ew_total_redeemed')}
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: '700', color: colors.warm, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ArrowDownRight size={20} />
              {wallet?.total_redeemed.toFixed(0)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.85rem', color: colors.textMuted, marginBottom: '8px' }}>
              {t('ew_transactions')}
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: '700', color: colors.accent }}>
              {stats?.transaction_count || 0}
            </div>
          </div>
        </motion.div>

        {/* Charts Row */}
        {stats?.monthly_flow && stats.monthly_flow.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
            {/* Monthly Flow Chart */}
            <motion.div
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              style={{
                background: colors.cardBg, padding: '24px', borderRadius: '20px',
                border: `1px solid ${colors.border}`,
              }}
            >
              <h3 style={{ color: colors.text, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <TrendingUp size={20} color={colors.success} />
                {t('ew_monthly_flow')}
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={stats.monthly_flow}>
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                  <XAxis dataKey="month" stroke={colors.textMuted} fontSize={11} />
                  <YAxis stroke={colors.textMuted} />
                  <Tooltip contentStyle={{ background: colors.bgAlt, border: `1px solid ${colors.border}`, borderRadius: '8px' }} />
                  <Legend />
                  <Bar dataKey="earned" fill="#10b981" name="Earned" radius={[8, 8, 0, 0]} />
                  <Bar dataKey="redeemed" fill="#f59e0b" name="Redeemed" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </motion.div>

            {/* Earning by Category Pie */}
            <motion.div
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              style={{
                background: colors.cardBg, padding: '24px', borderRadius: '20px',
                border: `1px solid ${colors.border}`,
              }}
            >
              <h3 style={{ color: colors.text, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Award size={20} color={colors.accent} />
                {t('ew_earning_by_category')}
              </h3>
              {stats?.earn_by_category && Object.keys(stats.earn_by_category).length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={Object.entries(stats.earn_by_category).map(([cat, val], i) => ({
                        name: cat,
                        value: val,
                      }))}
                      cx="50%" cy="50%"
                      innerRadius={50}
                      outerRadius={90}
                      paddingAngle={2}
                      dataKey="value"
                      label={(entry: any) => entry.name}
                    >
                      {Object.entries(stats.earn_by_category).map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ background: colors.bgAlt, border: `1px solid ${colors.border}` }} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px', color: colors.textMuted }}>
                  No earning data yet
                </div>
              )}
            </motion.div>
          </div>
        )}

        {/* Earn Options */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{
            background: colors.cardBg, padding: '24px', borderRadius: '20px',
            border: `1px solid ${colors.border}`, marginBottom: '24px',
          }}
        >
          <h3 style={{ color: colors.text, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrendingUp size={20} color={colors.success} />
            {t('ew_earn_eco')}
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '14px' }}>
            {earningOptions.map((opt, i) => (
              <motion.button
                key={opt.category}
                whileHover={{ y: -4, boxShadow: `0 8px 20px ${colors.success}20` }}
                whileTap={{ scale: 0.98 }}
                onClick={() => earn(opt.category)}
                style={{
                  padding: '18px', borderRadius: '14px',
                  background: colors.bg,
                  border: `1px solid ${colors.border}`,
                  cursor: 'pointer', textAlign: 'start',
                  fontFamily: 'inherit',
                  transition: 'all 0.2s',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <span style={{ fontSize: '1.8rem' }}>{opt.icon}</span>
                  <span style={{
                    padding: '4px 10px', borderRadius: '100px',
                    background: `${colors.success}15`, color: colors.success,
                    fontSize: '0.8rem', fontWeight: '700',
                  }}>
                    +{opt.eco_amount} ECO
                  </span>
                </div>
                <div style={{ fontSize: '0.9rem', color: colors.text, textTransform: 'capitalize' }}>
                  {opt.description}
                </div>
              </motion.button>
            ))}
          </div>
        </motion.div>

        {/* Redeem Options */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{
            background: colors.cardBg, padding: '24px', borderRadius: '20px',
            border: `1px solid ${colors.border}`, marginBottom: '24px',
          }}
        >
          <h3 style={{ color: colors.text, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShoppingBag size={20} color={colors.warm} />
            {t('ew_redeem_eco')}
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '14px' }}>
            {redemptionOptions.map((opt) => {
              const canAfford = (wallet?.balance || 0) >= opt.eco_cost;
              return (
                <motion.div
                  key={opt.category}
                  whileHover={canAfford ? { y: -4 } : {}}
                  style={{
                    padding: '18px', borderRadius: '14px',
                    background: canAfford ? colors.bg : `${colors.textMuted}10`,
                    border: `1px solid ${canAfford ? colors.border : colors.textMuted}30`,
                    opacity: canAfford ? 1 : 0.6,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <span style={{ fontSize: '2rem' }}>{opt.icon}</span>
                    <span style={{
                      padding: '4px 10px', borderRadius: '100px',
                      background: `${colors.warm}15`, color: colors.warm,
                      fontSize: '0.8rem', fontWeight: '700',
                    }}>
                      {opt.eco_cost} ECO
                    </span>
                  </div>
                  <div style={{ fontSize: '0.95rem', color: colors.text, marginBottom: '4px', fontWeight: '600' }}>
                    {opt.description}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: colors.textMuted, marginBottom: '10px' }}>
                    ≈ ${opt.value_usd} value
                  </div>
                  <button
                    onClick={() => redeem(opt.category)}
                    disabled={!canAfford}
                    style={{
                      width: '100%', padding: '8px', borderRadius: '8px',
                      background: canAfford ? colors.warm : colors.textMuted,
                      color: 'white', border: 'none', cursor: canAfford ? 'pointer' : 'not-allowed',
                      fontSize: '0.85rem', fontWeight: '600', fontFamily: 'inherit',
                    }}
                  >
                    {canAfford ? (t('ew_redeem')) : (t('ew_insufficient_balance'))}
                  </button>
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        {/* Transaction History */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{
            background: colors.cardBg, padding: '24px', borderRadius: '20px',
            border: `1px solid ${colors.border}`,
          }}
        >
          <h3 style={{ color: colors.text, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Zap size={20} color={colors.accent} />
            {t('ew_transaction_history')}
          </h3>
          {transactions.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: colors.textMuted }}>
              No transactions yet. Start earning ECO!
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '400px', overflowY: 'auto' }}>
              {transactions.map((tx) => (
                <div key={tx.transaction_id} style={{
                  padding: '14px', background: colors.bg, borderRadius: '10px',
                  display: 'flex', alignItems: 'center', gap: '14px',
                  border: `1px solid ${colors.border}`,
                }}>
                  <div style={{
                    width: '40px', height: '40px', borderRadius: '50%',
                    background: tx.transaction_type === 'earn' ? `${colors.success}15` : `${colors.warm}15`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    {tx.transaction_type === 'earn' 
                      ? <ArrowUpRight size={18} color={colors.success} />
                      : <ArrowDownRight size={18} color={colors.warm} />
                    }
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.9rem', fontWeight: '600', color: colors.text }}>
                      {tx.description}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: colors.textMuted }}>
                      {new Date(tx.timestamp).toLocaleString()}
                    </div>
                  </div>
                  <div style={{ textAlign: 'end' }}>
                    <div style={{
                      fontSize: '1.1rem', fontWeight: '700',
                      color: tx.transaction_type === 'earn' ? colors.success : colors.warm,
                    }}>
                      {tx.transaction_type === 'earn' ? '+' : '-'}{tx.amount.toFixed(2)}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: colors.textMuted }}>
                      Bal: {tx.balance_after.toFixed(2)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      </div>
      <Footer />
    </div>
  );
}
