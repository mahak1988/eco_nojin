/** Payments page — create and track payment intents. */

import { useState, useEffect } from 'react';
import { useBilingual } from '../../../hooks/useBilingual';
import { useAuth } from '../../../context/AuthContext';
import { createPaymentIntent } from '../../../lib/financeApi';
import { fetchOrders } from '../../../lib/commerceApi';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { CreditCard, Plus, Loader2, CheckCircle } from 'lucide-react';

export default function PaymentsPage() {
  const { fa } = useBilingual();
  const { isAdmin } = useAuth();
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ amount: '', currency: 'IRR', order_id: '', provider: 'wallet' });
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  async function load() {
    try {
      const o = await fetchOrders({ limit: 50 }).catch(() => null);
      if (o) setOrders(o.orders);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate() {
    setSubmitting(true);
    try {
      await createPaymentIntent({
        amount: form.amount,
        currency: form.currency,
        order_id: form.order_id,
        provider: form.provider,
        metadata: {},
      });
      setDone(true);
      setForm({ amount: '', currency: 'IRR', order_id: '', provider: 'wallet' });
      setTimeout(() => setDone(false), 2000);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <Seo title={fa('پرداخت‌ها', 'Payments')} path="/dashboard/finance/payments" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-5xl">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
              <CreditCard className="h-6 w-6 text-[var(--color-leaf-400)]" />
              {fa('پرداخت‌ها', 'Payments')}
            </h1>
            {isAdmin && (
              <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-2 rounded-xl bg-[var(--color-leaf-500)] px-4 py-2 text-sm font-extrabold text-[var(--color-night-950)]">
                <Plus className="h-4 w-4" /> {fa('پرداخت جدید', 'New Payment')}
              </button>
            )}
          </div>

          {showForm && (
            <Reveal>
              <div className="glass rounded-2xl p-6 mb-6">
                <h3 className="text-lg font-extrabold text-[var(--color-night-100)] mb-4">{fa('ایجاد پرداخت', 'Create Payment')}</h3>
                <div className="grid gap-3 lg:grid-cols-4">
                  <input placeholder="Amount" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                  <input placeholder="Currency" value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                  <input placeholder="Order ID" value={form.order_id} onChange={(e) => setForm({ ...form, order_id: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                  <select value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm">
                    <option value="wallet">Wallet</option><option value="cod">COD</option><option value="stripe">Stripe</option><option value="bank_transfer">Bank Transfer</option>
                  </select>
                </div>
                <button onClick={handleCreate} disabled={submitting || !form.amount || !form.order_id} className="mt-3 rounded-xl bg-[var(--color-leaf-500)] px-4 py-2 text-sm font-extrabold text-[var(--color-night-950)] disabled:opacity-50">
                  {submitting ? <Loader2 className="h-4 w-4 animate-spin inline" /> : null} {fa('ایجاد', 'Create')}
                </button>
                {done && <div className="mt-3 text-[var(--color-leaf-400)] font-bold"><CheckCircle className="inline h-4 w-4" /> {fa('پرداخت ایجاد شد', 'Payment created')}</div>}
              </div>
            </Reveal>
          )}

          {loading ? (
            <div className="flex items-center gap-2 text-sm text-[var(--color-night-200)]/60"><Loader2 className="h-4 w-4 animate-spin" />{fa('در حال بارگذاری...', 'Loading...')}</div>
          ) : (
            <Reveal delay={0.1}>
              <div className="glass rounded-2xl p-6">
                <h3 className="text-lg font-extrabold text-[var(--color-night-100)] mb-4">{fa('سفارشات مرتبط', 'Related Orders')}</h3>
                {orders.length === 0 ? (
                  <p className="text-sm text-[var(--color-night-200)]/60">{fa('هیچ سفارشی', 'No orders')}</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm" dir="ltr">
                      <thead><tr className="text-xs text-[var(--color-night-200)]/60 text-left">
                        <th className="pb-2">{fa('شناسه', 'ID')}</th><th className="pb-2">{fa('شماره', 'Number')}</th><th className="pb-2">{fa('وضعیت', 'Status')}</th><th className="pb-2">{fa('وضعیت پرداخت', 'Payment')}</th><th className="pb-2">{fa('مبلغ', 'Amount')}</th>
                      </tr></thead>
                      <tbody>
                        {orders.slice(0, 20).map((o) => (
                          <tr key={o.id} className="border-t border-[var(--color-night-200)]/10">
                            <td className="py-2 text-xs">{o.id.slice(0, 12)}</td>
                            <td className="py-2">{o.order_number}</td>
                            <td className="py-2">{o.status}</td>
                            <td className="py-2">{o.payment_status}</td>
                            <td className="py-2">{o.total} {o.currency}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </Reveal>
          )}
        </div>
      </div>
    </>
  );
}

