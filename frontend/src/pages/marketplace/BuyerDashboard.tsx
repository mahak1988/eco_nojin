import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useBilingual } from '../../hooks/useBilingual';
import { fetchOrders } from '../../lib/marketplaceApi';
import { ORDER_STATUS_LABEL, PAYMENT_STATUS_LABEL } from './catalog-shared';
import type { Order } from '../../lib/marketplaceTypes';
import Seo from '../../components/ui/Seo';
import Reveal from '../../components/ui/Reveal';
import { ClipboardList, ChevronDown, ChevronUp, Loader2, Truck, ExternalLink } from 'lucide-react';

export default function BuyerDashboard() {
  const { fa, lang } = useBilingual();
  const isFa = lang === 'fa';
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    fetchOrders().then((data) => { setOrders(data.orders); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const filtered = filter === 'all' ? orders : orders.filter((o) => o.status === filter);
  const stats = {
    total: orders.length,
    pending: orders.filter((o) => o.status === 'pending' || o.status === 'confirmed' || o.status === 'shipped').length,
    delivered: orders.filter((o) => o.status === 'delivered').length,
    cancelled: orders.filter((o) => o.status === 'cancelled').length,
  };

  return (
    <>
      <Seo title="سفارشات" path="/marketplace/orders" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-5xl">
          <h1 className="mb-6 text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2"><ClipboardList className="h-6 w-6 text-[var(--color-leaf-400)]" />{fa('سفارشات من', 'My Orders')}</h1>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[
              { label: fa('کل', 'Total'), value: stats.total, color: 'leaf' },
              { label: fa('در حال پردازش', 'Processing'), value: stats.pending, color: 'aqua' },
              { label: fa('تحویل شده', 'Delivered'), value: stats.delivered, color: 'leaf' },
              { label: fa('لغو شده', 'Cancelled'), value: stats.cancelled, color: 'red' },
            ].map((s) => (
              <div key={s.label} className="glass rounded-2xl p-4 text-center">
                <p className="text-3xl font-extrabold text-[var(--color-leaf-400)]">{s.value}</p>
                <p className="text-xs text-[var(--color-night-200)]/60">{s.label}</p>
              </div>
            ))}
          </div>
          <div className="flex gap-2 mb-4">
            {['all', 'pending', 'delivered', 'cancelled'].map((f) => (
              <button key={f} onClick={() => setFilter(f)} className={`rounded-full px-3 py-1.5 text-[11px] font-bold ${filter === f ? 'bg-[var(--color-leaf-500)] text-[var(--color-night-950)]' : 'border border-white/10 text-[var(--color-night-200)]/60'}`}>{fa({ all: 'همه', pending: 'در انتظار', delivered: 'تحویل شده', cancelled: 'لغو شده' }[f], { all: 'All', pending: 'Pending', delivered: 'Delivered', cancelled: 'Cancelled' }[f])}</button>
            ))}
          </div>
          {loading ? (
            <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-leaf-400" /></div>
          ) : filtered.length === 0 ? (
            <p className="text-center py-12 text-[var(--color-night-200)]/60">{fa('سفارشی یافت نشد', 'No orders')}</p>
          ) : (
            <div className="flex flex-col gap-3">
              {filtered.map((order) => (
                <Reveal key={order.id}>
                  <div className="glass rounded-2xl p-4">
                    <div className="flex items-center justify-between cursor-pointer" onClick={() => setExpanded(expanded === order.id ? null : order.id)}>
                      <div>
                        <p className="font-extrabold text-[var(--color-night-100)] text-sm">{fa('سفارش', 'Order')} #{order.order_number || order.id}</p>
                        <p className="text-[11px] text-[var(--color-night-200)]/50">{order.created_at ? new Date(order.created_at).toLocaleDateString(isFa ? 'fa-IR' : 'en-US') : ''}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="rounded-full bg-[var(--color-leaf-500)]/15 px-2 py-0.5 text-[10px] font-bold text-[var(--color-leaf-300)]">{ORDER_STATUS_LABEL[order.status]?.fa || order.status}{ORDER_STATUS_LABEL[order.status]?.en || order.status}</span>
                        {(order.status === 'pending' || order.status === 'confirmed' || order.status === 'shipped') && (
                          <Link to={`/marketplace/orders/${order.id}/track`} className="inline-flex items-center gap-1.5 text-xs font-bold text-[var(--color-leaf-400)] hover:text-[var(--color-leaf-300)]">
                            <Truck className="h-3.5 w-3.5" aria-hidden />
                            {fa('ردیابی', 'Track')}
                            <ExternalLink className="h-3 w-3" aria-hidden />
                          </Link>
                        )}
                        {expanded ? <ChevronUp className="h-4 w-4 text-[var(--color-night-200)]/50" /> : <ChevronDown className="h-4 w-4 text-[var(--color-night-200)]/50" />}
                      </div>
                    </div>
                    {expanded && (
                      <div className="mt-3 border-t border-white/10 pt-3 space-y-1">
                        <p className="text-xs text-[var(--color-night-200)]/60">{fa('وضعیت پرداخت:', 'Payment:')} {PAYMENT_STATUS_LABEL[order.payment_status]?.fa || order.payment_status}</p>
                        <p className="text-xs text-[var(--color-night-200)]/60">{fa('مبلغ:', 'Amount:')} {order.total.toLocaleString()} IRR</p>
                        <p className="text-xs text-[var(--color-night-200)]/60">{fa('تعداد اقلام:', 'Items:')} {order.items.length}</p>
                      </div>
                    )}
                  </div>
                </Reveal>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
