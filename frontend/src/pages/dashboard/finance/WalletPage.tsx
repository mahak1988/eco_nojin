/** Wallet page — earn and redeem ECO tokens. */

import { useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useBilingual } from '../../../hooks/useBilingual';
import { fetchWallet, earnTokens, redeemTokens } from '../../../lib/financeApi';
import { fetchWalletStats } from '../../../lib/financeApi';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { Wallet, Plus, Minus, Loader2, CheckCircle } from 'lucide-react';
import type { EarnRequest, RedeemRequest } from '../../../lib/financeTypes';

export default function WalletPage() {
  const { fa } = useBilingual();
  const { isAdmin } = useAuth();
  const [wallet, setWallet] = useState<Awaited<ReturnType<typeof fetchWallet>> | null>(null);
  const [stats, setStats] = useState<Awaited<ReturnType<typeof fetchWalletStats>> | null>(null);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState<'earn' | 'redeem' | null>(null);
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('tree_planting');
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  async function load() {
    const [w, s] = await Promise.all([fetchWallet().catch(() => null), fetchWalletStats().catch(() => null)]);
    if (w) setWallet(w);
    if (s) setStats(s);
    setLoading(false);
  }

  useState(() => { load(); });

  async function submitEarn() {
    setSubmitting(true);
    try {
      await earnTokens({ category: category as EarnRequest['category'], quantity: amount, idempotency_key: crypto.randomUUID() });
      setDone(true);
      setTimeout(() => { setDone(false); setAmount(''); load(); }, 2000);
    } finally {
      setSubmitting(false);
    }
  }

  async function submitRedeem() {
    setSubmitting(true);
    try {
      await redeemTokens({ category: category as RedeemRequest['category'], idempotency_key: crypto.randomUUID() });
      setDone(true);
      setTimeout(() => { setDone(false); setAmount(''); load(); }, 2000);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <Seo title={fa('کیف پول', 'Wallet')} path="/dashboard/finance/wallet" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-4xl">
          <h1 className="mb-6 text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
            <Wallet className="h-6 w-6 text-[var(--color-leaf-400)]" />
            {fa('کیف پول ECO', 'ECO Wallet')}
          </h1>

          {loading && (
            <div className="flex items-center gap-2 text-sm text-[var(--color-night-200)]/60">
              <Loader2 className="h-4 w-4 animate-spin" />
              {fa('در حال بارگذاری...', 'Loading...')}
            </div>
          )}

          {wallet && (
            <div className="grid grid-cols-3 gap-4 mb-8">
              <Reveal>
                <div className="glass rounded-2xl p-4 text-center">
                  <p className="text-3xl font-extrabold text-[var(--color-leaf-400)]">{wallet.balance}</p>
                  <p className="text-xs text-[var(--color-night-200)]/60">{fa('موجودی', 'Balance')}</p>
                </div>
              </Reveal>
              <Reveal delay={0.07}>
                <div className="glass rounded-2xl p-4 text-center">
                  <p className="text-3xl font-extrabold text-[var(--color-aqua-400)]">{wallet.total_earned}</p>
                  <p className="text-xs text-[var(--color-night-200)]/60">{fa('درآمد کل', 'Earned')}</p>
                </div>
              </Reveal>
              <Reveal delay={0.14}>
                <div className="glass rounded-2xl p-4 text-center">
                  <p className="text-3xl font-extrabold text-[var(--color-amber-400)]">{wallet.total_redeemed}</p>
                  <p className="text-xs text-[var(--color-night-200)]/60">{fa('خرج کل', 'Redeemed')}</p>
                </div>
              </Reveal>
            </div>
          )}

          {done && (
            <div className="glass rounded-2xl p-4 mb-6 text-[var(--color-leaf-400)] font-bold">
              <CheckCircle className="inline h-5 w-5 ml-1" /> {fa('عملیات با موفقیت انجام شد', 'Operation successful')}
            </div>
          )}

          <Reveal delay={0.21}>
            <div className="glass rounded-2xl p-6 mb-6">
              <h2 className="text-lg font-extrabold text-[var(--color-night-100)] mb-4">
                {fa('عملیات جدید', 'New Operation')}
              </h2>
              <div className="grid gap-4 lg:grid-cols-3">
                <div>
                  <label className="text-xs text-[var(--color-night-200)]/60">{fa('نوع', 'Type')}</label>
                  <select
                    value={action ?? 'earn'}
                    onChange={(e) => setAction(e.target.value as 'earn' | 'redeem')}
                    className="w-full rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm text-[var(--color-night-100)]"
                  >
                    <option value="earn">{fa('کسب', 'Earn')}</option>
                    <option value="redeem">{fa('صرف', 'Redeem')}</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-[var(--color-night-200)]/60">{fa('مبلغ', 'Amount')}</label>
                  <input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="0"
                    className="w-full rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm text-[var(--color-night-100)]"
                  />
                </div>
                <div>
                  <label className="text-xs text-[var(--color-night-200)]/60">{fa('دسته‌بندی', 'Category')}</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm text-[var(--color-night-100)]"
                  >
                    <option value="tree_planting">{fa('کاشت درخت', 'Tree Planting')}</option>
                    <option value="soil_health">{fa('سلامت خاک', 'Soil Health')}</option>
                    <option value="water_saving">{fa('صرفه‌جویی آب', 'Water Saving')}</option>
                    <option value="carbon_credit">{fa('کربن', 'Carbon Credit')}</option>
                    <option value="education">{fa('آموزش', 'Education')}</option>
                    <option value="community">{fa('جامعه', 'Community')}</option>
                  </select>
                </div>
              </div>
              <div className="mt-4 flex gap-3">
                {action !== 'redeem' && (
                  <button
                    onClick={submitEarn}
                    disabled={submitting || !amount}
                    className="flex items-center gap-2 rounded-xl bg-[var(--color-leaf-500)] px-5 py-2.5 text-sm font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-105 disabled:opacity-50"
                  >
                    <Plus className="h-4 w-4" /> {fa('کسب', 'Earn')}
                  </button>
                )}
                {action !== 'earn' && (
                  <button
                    onClick={submitRedeem}
                    disabled={submitting || !amount}
                    className="flex items-center gap-2 rounded-xl bg-[var(--color-amber-500)] px-5 py-2.5 text-sm font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-105 disabled:opacity-50"
                  >
                    <Minus className="h-4 w-4" /> {fa('صرف', 'Redeem')}
                  </button>
                )}
              </div>
            </div>
          </Reveal>

          {isAdmin && stats && (
            <Reveal delay={0.28}>
              <div className="glass rounded-2xl p-6">
                <h3 className="text-lg font-extrabold text-[var(--color-night-100)] mb-4">{fa('آمار کل', 'Global Stats')}</h3>
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div className="text-[var(--color-night-200)]/60">{fa('کیف‌های فعال', 'Active Wallets')}: {stats.total_wallets}</div>
                  <div className="text-[var(--color-night-200)]/60">{fa('توکن صادر شده', 'Issued')}: {stats.total_tokens_issued}</div>
                  <div className="text-[var(--color-night-200)]/60">{fa('توکن کسب شده', 'Earned')}: {stats.total_tokens_earned}</div>
                  <div className="text-[var(--color-night-200)]/60">{fa('توکن صرف شده', 'Redeemed')}: {stats.total_tokens_redeemed}</div>
                </div>
              </div>
            </Reveal>
          )}
        </div>
      </div>
    </>
  );
}


