/** Finance Dashboard — wallet balance, payment intents, reconciliation summary. */

import { useState, useEffect } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useBilingual } from '../../../hooks/useBilingual';
import { fetchWallet, reconcileWalletLedger } from '../../../lib/financeApi';
import { fetchOrders } from '../../../lib/commerceApi';
import type { Order } from '../../../lib/commerceTypes';
import type { ReconciliationResult } from '../../../lib/financeTypes';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { Wallet, RefreshCw, ShoppingCart, Loader2, CheckCircle } from 'lucide-react';

export default function FinanceDashboard() {
  const { fa } = useBilingual();
  const { isAdmin } = useAuth();
  const [wallet, setWallet] = useState<{ balance: string; total_earned: string; total_redeemed: string } | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [orderCount, setOrderCount] = useState<number>(0);
  const [recon, setRecon] = useState<ReconciliationResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [w, o] = await Promise.all([
          fetchWallet().catch(() => null),
          fetchOrders({ limit: 20 }).catch(() => null),
        ]);
        if (w) setWallet(w);
        if (o) { setOrders(o.orders); setOrderCount(o.count); }
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const pendingOrders = orders.filter((o) => o.payment_status === 'pending' || o.payment_status === 'authorized');

  return (
    <>
      <Seo title={fa('داشبورد مالی', 'Finance Dashboard')} path="/dashboard/finance" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-6xl">
          <h1 className="mb-6 text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
            <Wallet className="h-6 w-6 text-[var(--color-leaf-400)]" />
            {fa('داشبورد مالی', 'Finance Dashboard')}
          </h1>

          {loading && (
            <div className="flex items-center gap-2 text-sm text-[var(--color-night-200)]/60">
              <Loader2 className="h-4 w-4 animate-spin" />
              {fa('در حال بارگذاری...', 'Loading...')}
            </div>
          )}

          {/* --- Stats --- */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <Reveal delay={0}>
              <div className="glass rounded-2xl p-4 text-center">
                <p className="text-3xl font-extrabold text-[var(--color-leaf-400)]">
                  {wallet ? Number(wallet.balance).toLocaleString() : '-'}
                </p>
                <p className="text-xs text-[var(--color-night-200)]/60">{fa('موجودی کیف پول', 'Wallet Balance')}</p>
              </div>
            </Reveal>
            <Reveal delay={0.07}>
              <div className="glass rounded-2xl p-4 text-center">
                <p className="text-3xl font-extrabold text-[var(--color-aqua-400)]">
                  {wallet ? Number(wallet.total_earned).toLocaleString() : '-'}
                </p>
                <p className="text-xs text-[var(--color-night-200)]/60">{fa('کل درآمد', 'Total Earned')}</p>
              </div>
            </Reveal>
            <Reveal delay={0.14}>
              <div className="glass rounded-2xl p-4 text-center">
                <p className="text-3xl font-extrabold text-[var(--color-amber-400)]">
                  {wallet ? Number(wallet.total_redeemed).toLocaleString() : '-'}
                </p>
                <p className="text-xs text-[var(--color-night-200)]/60">{fa('کل خرج', 'Total Redeemed')}</p>
              </div>
            </Reveal>
            <Reveal delay={0.21}>
              <div className="glass rounded-2xl p-4 text-center">
                <p className="text-3xl font-extrabold text-[var(--color-leaf-400)]">
                  {orderCount}
                </p>
                <p className="text-xs text-[var(--color-night-200)]/60">{fa('سفارشات', 'Orders')}</p>
              </div>
            </Reveal>
          </div>

          {/* --- Quick Actions --- */}
          <div className="grid gap-4 lg:grid-cols-3 mb-8">
            <Reveal>
              <a
                href="#orders"
                className="glass glass-hover rounded-2xl p-6 block transition-all"
              >
                <ShoppingCart className="h-8 w-8 text-[var(--color-leaf-400)] mb-3" />
                <h3 className="text-base font-extrabold text-[var(--color-night-100)]">{fa('مدیریت سفارشات', 'Orders')}</h3>
                <p className="mt-2 text-sm text-[var(--color-night-200)]/60">
                  {fa(`${pendingOrders.length} سفارش در حال پردازش`, `${pendingOrders.length} orders pending`)}
                </p>
              </a>
            </Reveal>
            {isAdmin && (
              <Reveal delay={0.07}>
                <button
                  onClick={async () => {
                    try {
                      const r = await reconcileWalletLedger();
                      setRecon(r);
                    } catch { /* noop */ }
                  }}
                  className="w-full glass glass-hover rounded-2xl p-6 text-right transition-all"
                >
                  <RefreshCw className="h-8 w-8 text-[var(--color-aqua-400)] mb-3 ml-auto" />
                  <h3 className="text-base font-extrabold text-[var(--color-night-100)]">{fa('تطبیق کیف با دفتر', 'Reconcile')}</h3>
                  <p className="mt-2 text-sm text-[var(--color-night-200)]/60 text-left" dir="ltr">
                    {fa('تطبیق حسابداری کیف پول با دفتر سهامداری', 'Reconcile wallet with ledger')}
                  </p>
                </button>
              </Reveal>
            )}
            <Reveal delay={0.14}>
              <a
                href="#ledger"
                className="glass glass-hover rounded-2xl p-6 block transition-all"
              >
                <CheckCircle className="h-8 w-8 text-[var(--color-leaf-400)] mb-3" />
                <h3 className="text-base font-extrabold text-[var(--color-night-100)]">{fa('دفتر سهامداری', 'Ledger')}</h3>
                <p className="mt-2 text-sm text-[var(--color-night-200)]/60">
                  {fa('ورودی‌ها و خروجی‌های دفتری', 'Journal entries')}
                </p>
              </a>
            </Reveal>
          </div>

          {recon && (
            <div className="glass rounded-2xl p-6 mb-8">
              <h3 className="flex items-center gap-2 text-base font-extrabold text-[var(--color-night-100)] mb-4">
                <RefreshCw className="h-5 w-5 text-[var(--color-aqua-400)]" />
                {fa('نتیجه تطبیق', 'Reconciliation Result')}
              </h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="text-[var(--color-night-200)]/60">{fa('تعداد کل بررسی', 'Total Checked')}: {recon.total_checked}</div>
                <div className="text-[var(--color-night-200)]/60">{fa('اختلافات', 'Discrepancies')}: {recon.discrepancies_count}</div>
                <div className="col-span-2">
                  {recon.overall_ok ? (
                    <span className="text-[var(--color-leaf-400)] font-bold">{fa('کلیه تطبیق‌ها درست هستند ✓', 'All reconciliations OK ✓')}</span>
                  ) : (
                    <span className="text-[#e8c66b] font-bold">{fa('بررسی اختلافات لازم است', 'Discrepancies found')}</span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* --- Recent Orders --- */}
          <Reveal delay={0.21}>
            <div id="orders" className="glass rounded-2xl p-6">
              <h3 className="flex items-center gap-2 text-base font-extrabold text-[var(--color-night-100)] mb-4">
                <ShoppingCart className="h-5 w-5 text-[var(--color-leaf-400)]" />
                {fa('سفارشات اخیر', 'Recent Orders')}
              </h3>
              {orders.length === 0 ? (
                <p className="text-sm text-[var(--color-night-200)]/60">{fa('هیچ سفارشی ثبت نشده', 'No orders found')}</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm" dir="ltr">
                    <thead>
                      <tr className="text-xs text-[var(--color-night-200)]/60 text-left">
                        <th className="pb-2">{fa('شناسه', 'ID')}</th>
                        <th className="pb-2">{fa('مبلغ', 'Amount')}</th>
                        <th className="pb-2">{fa('وضعیت', 'Status')}</th>
                        <th className="pb-2">{fa('وضعیت پرداخت', 'Payment')}</th>
                        <th className="pb-2">{fa('تاریخ', 'Date')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {orders.slice(0, 10).map((o) => (
                        <tr key={o.id} className="border-t border-[var(--color-night-200)]/10">
                          <td className="py-2 font-mono text-xs">{o.order_number.slice(0, 16)}</td>
                          <td className="py-2">{o.total} {o.currency}</td>
                          <td className="py-2">
                            <span className="rounded-full px-2 py-0.5 text-xs bg-[var(--color-leaf-500)]/20 text-[var(--color-leaf-400)]">{o.status}</span>
                          </td>
                          <td className="py-2">
                            <span className={`rounded-full px-2 py-0.5 text-xs ${o.payment_status === 'paid' ? 'bg-[var(--color-leaf-500)]/20 text-[var(--color-leaf-400)]' : 'bg-[#e8c66b]/20 text-[#e8c66b]'}`}>
                              {o.payment_status}
                            </span>
                          </td>
                          <td className="py-2 text-xs">{new Date(o.created_at).toLocaleDateString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </Reveal>
        </div>
      </div>
    </>
  );
}


