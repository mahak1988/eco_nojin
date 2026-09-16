/** Commerce Payments - Payment intents and transaction management */

import { useState, useEffect } from 'react';
import { useBilingual } from '../../../hooks/useBilingual';
import { fetchOrders, payOrder, confirmPayment } from '../../../lib/commerceApi';
import type { Order, PaymentStatus } from '../../../lib/commerceTypes';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { CreditCard, Loader2, AlertCircle, Search, Filter, CheckCircle, XCircle, Clock, DollarSign } from 'lucide-react';

const PAYMENT_STATUS_LABELS: Record<PaymentStatus, { fa: string; en: string; color: string }> = {
  pending: { fa: 'در انتظار', en: 'Pending', color: 'yellow' },
  authorized: { fa: 'تأیید شده', en: 'Authorized', color: 'blue' },
  paid: { fa: 'پرداخت شده', en: 'Paid', color: 'green' },
  failed: { fa: 'ناموفق', en: 'Failed', color: 'red' },
  refunded: { fa: 'بازپرداخت', en: 'Refunded', color: 'orange' },
  partial_refund: { fa: 'بازپرداخت جزئی', en: 'Partial Refund', color: 'yellow' },
};

const paymentStatusColors: Record<string, string> = {
  green: 'bg-[var(--color-leaf-500)]/20 text-[var(--color-leaf-400)]',
  yellow: 'bg-[#e8c66b]/20 text-[#e8c66b]',
  blue: 'bg-[var(--color-aqua-500)]/20 text-[var(--color-aqua-400)]',
  red: 'bg-red-500/20 text-red-400',
  orange: 'bg-orange-500/20 text-orange-400',
};

export default function CommercePaymentsPage() {
  const { fa } = useBilingual();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchOrders(statusFilter ? { status: statusFilter } : { limit: 50 });
      setOrders(res.orders);
    } catch (err: any) {
      setError(err.message || fa('خطا در بارگذاری', 'Failed to load'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [statusFilter]);

  const handlePay = async (orderId: string) => {
    setActionLoading(orderId);
    try {
      await payOrder(orderId, 'wallet');
      loadData();
    } catch (err: any) {
      alert(fa('خطا: ' + (err.message || 'نامشخص'), 'Error: ' + (err.message || 'Unknown')));
    } finally {
      setActionLoading(null);
    }
  };

  const handleConfirm = async (orderId: string) => {
    setActionLoading(orderId);
    try {
      await confirmPayment(orderId);
      loadData();
    } catch (err: any) {
      alert(fa('خطا: ' + (err.message || 'نامشخص'), 'Error: ' + (err.message || 'Unknown')));
    } finally {
      setActionLoading(null);
    }
  };

  const pendingPayments = orders.filter(o => o.payment_status === 'pending' || o.payment_status === 'authorized');
  const paidCount = orders.filter(o => o.payment_status === 'paid').length;
  const failedCount = orders.filter(o => o.payment_status === 'failed').length;

  const paymentStatusColors: Record<string, string> = {
    green: 'bg-[var(--color-leaf-500)]/20 text-[var(--color-leaf-400)]',
    yellow: 'bg-[#e8c66b]/20 text-[#e8c66b]',
    blue: 'bg-[var(--color-aqua-500)]/20 text-[var(--color-aqua-400)]',
    red: 'bg-red-500/20 text-red-400',
    orange: 'bg-orange-500/20 text-orange-400',
  };

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-[var(--color-leaf-400)]" /></div>;
  if (error) return <div className="p-6 text-center text-red-400">{error}</div>;

  return (
    <>
      <Seo title={fa('مدیریت پرداخت‌ها', 'Payments Management')} path="/dashboard/commerce/payments" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-7xl">
          <h1 className="mb-6 text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
            <CreditCard className="h-6 w-6 text-[var(--color-leaf-400)]" />
            {fa('مدیریت پرداخت‌ها', 'Payments Management')}
          </h1>

          {/* Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <Reveal delay={0}><div className="glass rounded-2xl p-4 text-center"><p className="text-3xl font-extrabold text-[#e8c66b]">{pendingPayments.length}</p><p className="text-xs text-[var(--color-night-200)]/60">{fa('در انتظار پرداخت', 'Pending Payments')}</p></div></Reveal>
            <Reveal delay={0.07}><div className="glass rounded-2xl p-4 text-center"><p className="text-3xl font-extrabold text-[var(--color-aqua-400)]">{orders.filter(o => o.payment_status === 'authorized').length}</p><p className="text-xs text-[var(--color-night-200)]/60">{fa('تأیید شده', 'Authorized')}</p></div></Reveal>
            <Reveal delay={0.14}><div className="glass rounded-2xl p-4 text-center"><p className="text-3xl font-extrabold text-[var(--color-leaf-400)]">{paidCount}</p><p className="text-xs text-[var(--color-night-200)]/60">{fa('پرداخت شده', 'Paid')}</p></div></Reveal>
            <Reveal delay={0.21}><div className="glass rounded-2xl p-4 text-center"><p className="text-3xl font-extrabold text-red-400">{failedCount}</p><p className="text-xs text-[var(--color-night-200)]/60">{fa('ناموفق', 'Failed')}</p></div></Reveal>
          </div>

          {/* Filter */}
          <Reveal delay={0.3}>
            <div className="glass rounded-2xl p-4 mb-6 flex flex-wrap items-center gap-3">
              <span className="text-sm font-medium text-[var(--color-night-200)]/80">{fa('فیلتر وضعیت پرداخت:', 'Payment Status:')}</span>
              <div className="flex flex-wrap gap-2">
                {['', 'pending', 'authorized', 'paid', 'failed', 'refunded', 'partial_refund'].map(s => (
                  <button key={s} onClick={() => setStatusFilter(s)} className={`px-3 py-1.5 rounded-xl text-xs font-medium transition ${statusFilter === s ? 'bg-[var(--color-leaf-500)] text-white' : 'bg-[var(--color-night-50)] text-[var(--color-night-200)]/70 hover:bg-[var(--color-leaf-500)]/10 hover:text-[var(--color-leaf-400)]'}`}>{fa === 'fa' ? (PAYMENT_STATUS_LABELS[s as PaymentStatus]?.fa || s) : (PAYMENT_STATUS_LABELS[s as PaymentStatus]?.en || s)}</button>
                ))}
              </div>
            </div>
          </Reveal>

          {/* Payments Table */}
          <Reveal delay={0.4}>
            <div className="glass rounded-2xl overflow-hidden">
              {loading && <div className="p-8 text-center"><Loader2 className="h-8 w-8 animate-spin text-[var(--color-leaf-400)] mx-auto" /></div>}
              <div className="overflow-x-auto">
                <table className="w-full text-sm" dir="ltr">
                  <thead className="bg-[#f6ecd6]"><tr className="text-[var(--color-night-200)]/60 text-[11px] uppercase">
                    <th className="text-right p-3">{fa('سفارش', 'Order')}</th>
                    <th className="p-3">{fa('مبلغ', 'Amount')}</th>
                    <th className="p-3">{fa('پرداخت', 'Payment')}</th>
                    <th className="p-3">{fa('ارائه‌دهنده', 'Provider')}</th>
                    <th className="p-3">{fa('تاریخ', 'Date')}</th>
                    <th className="p-3">{fa('عملیات', 'Actions')}</th>
                  </tr></thead>
                  <tbody>
                    {orders.length === 0 ? (
                      <tr><td colSpan={6} className="p-6 text-center text-[var(--color-night-200)]/50">{fa('پرداختی یافت نشد', 'No payments found')}</td></tr>
                    ) : orders.map((order) => (
                      <tr key={order.id} className="border-t border-white/5">
                        <td className="text-right p-3 font-mono text-xs text-[var(--color-night-100)]">{order.order_number}</td>
                        <td className="p-3 font-bold text-[var(--color-night-100)]">{Number(order.total).toLocaleString()} {order.currency}</td>
                        <td className="p-3"><span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${paymentStatusColors[PAYMENT_STATUS_LABELS[order.payment_status]?.color] || 'bg-gray-500/20 text-gray-400'}`}>{fa === 'fa' ? PAYMENT_STATUS_LABELS[order.payment_status].fa : PAYMENT_STATUS_LABELS[order.payment_status].en}</span></td>
                        <td className="p-3 text-[var(--color-night-200)]/70 text-xs">Wallet</td>
                        <td className="p-3 text-xs text-[var(--color-night-200)]/60">{order.paid_at ? new Date(order.paid_at).toLocaleDateString() : new Date(order.created_at).toLocaleDateString()}</td>
                        <td className="p-3">
                          <div className="flex items-center gap-2">
                            {(order.payment_status === 'pending' || order.payment_status === 'authorized') && (
                              <button onClick={() => handlePay(order.id)} disabled={actionLoading === order.id} className="flex items-center gap-1.5 rounded-xl bg-[var(--color-leaf-500)] px-3 py-2 text-xs font-extrabold text-white transition hover:bg-[var(--color-leaf-600)] disabled:opacity-50">
                                {actionLoading === order.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CreditCard className="h-3.5 w-3.5" />}
                                {order.payment_status === 'authorized' ? fa('تأیید', 'Confirm') : fa('پرداخت', 'Pay')}
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </Reveal>
        </div>
      </div>
    </>
  );
}