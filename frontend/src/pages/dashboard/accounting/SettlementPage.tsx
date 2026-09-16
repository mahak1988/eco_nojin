/** Accounting Settlement page — order settlements for sellers. */

import { useState, useEffect } from 'react';
import { useBilingual } from '../../../hooks/useBilingual';
import { fetchOrders, settleOrder } from '../../../lib/commerceApi';
import { fetchSettlements } from '../../../lib/commerceApi';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { Receipt, Loader2 } from 'lucide-react';

export default function SettlementPage() {
  const { fa } = useBilingual();
  const [orders, setOrders] = useState<any[]>([]);
  const [settlements, setSettlements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    try {
      const [o, s] = await Promise.all([
        fetchOrders({ limit: 50 }).catch(() => null),
        fetchSettlements().catch(() => []),
      ]);
      if (o) setOrders(o.orders);
      if (s) setSettlements(s);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleSettle(orderId: string) {
    setSubmitting(true);
    try {
      await settleOrder(orderId);
      load();
    } catch { /* noop */ }
    setSubmitting(false);
  }

  const settledOrders = orders.filter((o) => o.status === 'settled');

  return (
    <>
      <Seo title={fa('تسویه حساب', 'Settlement')} path="/dashboard/accounting/settlement" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-5xl">
          <h1 className="mb-6 text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
            <Receipt className="h-6 w-6 text-[var(--color-leaf-400)]" />
            {fa('تسویه حساب', 'Settlement')}
          </h1>

          {loading && <div className="flex items-center gap-2 text-sm text-[var(--color-night-200)]/60"><Loader2 className="h-4 w-4 animate-spin" />{fa('در حال بارگذاری...', 'Loading...')}</div>}

          <Reveal>
            <div className="glass rounded-2xl p-6 mb-6">
              <h3 className="text-lg font-extrabold text-[var(--color-night-100)] mb-4">{fa('خلاصه', 'Summary')}</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-2xl font-extrabold text-[var(--color-leaf-400)]">{orders.length}</p>
                  <p className="text-xs text-[var(--color-night-200)]/60">{fa('سفارشات', 'Orders')}</p>
                </div>
                <div>
                  <p className="text-2xl font-extrabold text-[var(--color-aqua-400)]">{settlements.length}</p>
                  <p className="text-xs text-[var(--color-night-200)]/60">{fa('تسویه‌ها', 'Settlements')}</p>
                </div>
                <div>
                  <p className="text-2xl font-extrabold text-[var(--color-amber-400)]">{settledOrders.length}</p>
                  <p className="text-xs text-[var(--color-night-200)]/60">{fa('تسویه شده', 'Settled')}</p>
                </div>
              </div>
            </div>
          </Reveal>

          <Reveal delay={0.1}>
            <div className="glass rounded-2xl p-6">
              <h3 className="text-lg font-extrabold text-[var(--color-night-100)] mb-4">{fa('سفارشات قابل تسویه', 'Settlable Orders')}</h3>
              {orders.filter((o) => o.status === 'delivered').length === 0 ? (
                <p className="text-sm text-[var(--color-night-200)]/60">{fa('سفارش تحویل‌داده‌شده برای تسویه وجود ندارد', 'No delivered orders')}</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm" dir="ltr">
                    <thead><tr className="text-xs text-[var(--color-night-200)]/60 text-left">
                      <th className="pb-2">{fa('شماره', 'Number')}</th><th className="pb-2">{fa('مبلغ', 'Amount')}</th><th className="pb-2">{fa('وضعیت', 'Status')}</th><th className="pb-2">{fa('عملیات', 'Action')}</th>
                    </tr></thead>
                    <tbody>
                      {orders.filter((o) => o.status === 'delivered').slice(0, 20).map((o) => (
                        <tr key={o.id} className="border-t border-[var(--color-night-200)]/10">
                          <td className="py-2">{o.order_number}</td>
                          <td className="py-2">{o.total} {o.currency}</td>
                          <td className="py-2">{o.status}</td>
                          <td className="py-2">
                            <button onClick={() => handleSettle(o.id)} disabled={submitting} className="rounded-lg bg-[var(--color-leaf-500)] px-2 py-1 text-xs font-extrabold text-[var(--color-night-950)] disabled:opacity-50">
                              {fa('تسویه', 'Settle')}
                            </button>
                          </td>
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


