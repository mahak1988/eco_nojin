/** Commerce Orders - Detailed order management page */

import { useState, useEffect } from 'react';
import { useBilingual } from '../../../hooks/useBilingual';
import { fetchOrders, fetchOrder, payOrder, confirmPayment, shipOrder, markDelivered, cancelOrder, settleOrder, getAllowedTransitions } from '../../../lib/commerceApi';
import type { Order, OrderStatus, PaymentStatus } from '../../../lib/commerceTypes';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { ShoppingCart, Search, Filter, Loader2, AlertCircle, ChevronLeft, ChevronRight, MoreVertical, Eye, Edit, Truck, CreditCard, CheckCircle2, RotateCcw, XCircle } from 'lucide-react';

const STATUS_LABELS: Record<OrderStatus, { fa: string; en: string; color: string }> = {
  draft: { fa: 'پیش‌نویس', en: 'Draft', color: 'gray' },
  reserved: { fa: 'رزرو شده', en: 'Reserved', color: 'blue' },
  paid: { fa: 'پرداخت شده', en: 'Paid', color: 'green' },
  processing: { fa: 'در پردازش', en: 'Processing', color: 'yellow' },
  shipped: { fa: 'ارسال شده', en: 'Shipped', color: 'blue' },
  delivered: { fa: 'تحویل داده شده', en: 'Delivered', color: 'green' },
  settled: { fa: 'تسویه شده', en: 'Settled', color: 'purple' },
  cancelled: { fa: 'لغو شده', en: 'Cancelled', color: 'red' },
  refunded: { fa: 'بازپرداخت شده', en: 'Refunded', color: 'orange' },
};

const PAYMENT_STATUS_LABELS: Record<PaymentStatus, { fa: string; en: string; color: string }> = {
  pending: { fa: 'در انتظار', en: 'Pending', color: 'yellow' },
  authorized: { fa: 'تأیید شده', en: 'Authorized', color: 'blue' },
  paid: { fa: 'پرداخت شده', en: 'Paid', color: 'green' },
  failed: { fa: 'ناموفق', en: 'Failed', color: 'red' },
  refunded: { fa: 'بازپرداخت', en: 'Refunded', color: 'orange' },
  partial_refund: { fa: 'بازپرداخت جزئی', en: 'Partial Refund', color: 'yellow' },
};

const statusColors: Record<string, string> = {
  green: 'bg-[var(--color-leaf-500)]/20 text-[var(--color-leaf-400)]',
  yellow: 'bg-[#e8c66b]/20 text-[#e8c66b]',
  blue: 'bg-[var(--color-aqua-500)]/20 text-[var(--color-aqua-400)]',
  purple: 'bg-purple-500/20 text-purple-400',
  red: 'bg-red-500/20 text-red-400',
  orange: 'bg-orange-500/20 text-orange-400',
  gray: 'bg-gray-500/20 text-gray-400',
};

const paymentStatusColors: Record<string, string> = {
  green: 'bg-[var(--color-leaf-500)]/20 text-[var(--color-leaf-400)]',
  yellow: 'bg-[#e8c66b]/20 text-[#e8c66b]',
  blue: 'bg-[var(--color-aqua-500)]/20 text-[var(--color-aqua-400)]',
  red: 'bg-red-500/20 text-red-400',
  orange: 'bg-orange-500/20 text-orange-400',
};

export default function CommerceOrdersPage() {
  const { fa } = useBilingual();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const LIMIT = 20;

  const loadOrders = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = { limit: LIMIT, offset: (page - 1) * LIMIT };
      if (statusFilter) params.status = statusFilter;
      const res = await fetchOrders(params);
      setOrders(res.orders);
      setTotalCount(res.count);
    } catch (err: any) {
      setError(err.message || fa('خطا در بارگذاری', 'Failed to load'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadOrders(); }, [page, statusFilter]);

  const filteredOrders = searchQuery
    ? orders.filter(o =>
        o.order_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
        o.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        o.buyer_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (o.seller_id && o.seller_id.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    : orders;

  const handleAction = async (orderId: string, action: 'pay' | 'confirm' | 'ship' | 'deliver' | 'cancel' | 'settle', extraData?: { trackingCode?: string; reason?: string }) => {
    setActionLoading(orderId);
    try {
      switch (action) {
        case 'pay': await payOrder(orderId, 'wallet'); break;
        case 'confirm': await confirmPayment(orderId); break;
        case 'ship': if (extraData?.trackingCode) await shipOrder(orderId, extraData.trackingCode); break;
        case 'deliver': await markDelivered(orderId); break;
        case 'cancel': if (extraData?.reason) await cancelOrder(orderId, extraData.reason); break;
        case 'settle': await settleOrder(orderId); break;
      }
      loadOrders();
    } catch (err: any) {
      alert(fa('خطا: ' + (err.message || 'نامشخص'), 'Error: ' + (err.message || 'Unknown')));
    } finally {
      setActionLoading(null);
    }
  };

  const statusColors: Record<string, string> = {
    green: 'bg-[var(--color-leaf-500)]/20 text-[var(--color-leaf-400)]',
    yellow: 'bg-[#e8c66b]/20 text-[#e8c66b]',
    blue: 'bg-[var(--color-aqua-500)]/20 text-[var(--color-aqua-400)]',
    purple: 'bg-purple-500/20 text-purple-400',
    red: 'bg-red-500/20 text-red-400',
    orange: 'bg-orange-500/20 text-orange-400',
    gray: 'bg-gray-500/20 text-gray-400',
  };

  const paymentStatusColors: Record<string, string> = {
    green: 'bg-[var(--color-leaf-500)]/20 text-[var(--color-leaf-400)]',
    yellow: 'bg-[#e8c66b]/20 text-[#e8c66b]',
    blue: 'bg-[var(--color-aqua-500)]/20 text-[var(--color-aqua-400)]',
    red: 'bg-red-500/20 text-red-400',
    orange: 'bg-orange-500/20 text-orange-400',
  };

  if (loading && page === 1) return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-[var(--color-leaf-400)]" /></div>;
  if (error) return <div className="p-6 text-center text-red-400">{error}</div>;

  const totalPages = Math.ceil(totalCount / LIMIT);

  return (
    <>
      <Seo title={fa('مدیریت سفارشات', 'Orders Management')} path="/dashboard/commerce/orders" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-7xl">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
            <div>
              <h1 className="text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
                <ShoppingCart className="h-6 w-6 text-[var(--color-leaf-400)]" />
                {fa('مدیریت سفارشات', 'Orders Management')}
              </h1>
              <p className="mt-1 text-sm text-[var(--color-night-200)]/60">{fa('نمایش و مدیریت تمام سفارشات تجاری', 'View and manage all commerce orders')}</p>
            </div>
            <div className="flex flex-wrap gap-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-night-200)]/50" />
                <input
                  type="text"
                  placeholder={fa('جستجو در سفارشات...', 'Search orders...')}
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="pl-10 pr-4 py-2 bg-[var(--color-night-50)] border border-[var(--color-night-200)]/20 rounded-xl text-sm text-[var(--color-night-100)] focus:outline-none focus:ring-2 focus:ring-[var(--color-leaf-400)] w-64"
                />
              </div>
              <Filter className="h-5 w-5 text-[var(--color-night-200)]/60 self-center ml-2" />
            </div>
          </div>

          {/* Status Filter */}
          <Reveal delay={0.1}>
            <div className="glass rounded-2xl p-4 mb-6 flex flex-wrap items-center gap-3">
              <span className="text-sm font-medium text-[var(--color-night-200)]/80">{fa('فیلتر وضعیت:', 'Status:')}</span>
              <div className="flex flex-wrap gap-2">
                {['', 'draft', 'reserved', 'paid', 'processing', 'shipped', 'delivered', 'settled', 'cancelled', 'refunded'].map(s => (
                  <button
                    key={s}
                    onClick={() => { setStatusFilter(s); setPage(1); }}
                    className={`px-3 py-1.5 rounded-xl text-xs font-medium transition ${statusFilter === s
                      ? 'bg-[var(--color-leaf-500)] text-white'
                      : 'bg-[var(--color-night-50)] text-[var(--color-night-200)]/70 hover:bg-[var(--color-leaf-500)]/10 hover:text-[var(--color-leaf-400)]'
                    }`}
                  >
                    {fa === 'fa' ? (STATUS_LABELS[s as OrderStatus]?.fa || s) : (STATUS_LABELS[s as OrderStatus]?.en || s)}
                  </button>
                ))}
              </div>
            </div>
          </Reveal>

          {/* Orders Table */}
          <Reveal delay={0.2}>
            <div className="glass rounded-2xl overflow-hidden">
              {loading && page === 1 && (
                <div className="p-8 text-center"><Loader2 className="h-8 w-8 animate-spin text-[var(--color-leaf-400)] mx-auto" /></div>
              )}
              <div className="overflow-x-auto">
                <table className="w-full text-sm" dir="ltr">
                  <thead className="bg-[#f6ecd6]">
                    <tr className="text-[var(--color-night-200)]/60 text-[11px] uppercase">
                      <th className="text-right p-3">{fa('شماره سفارش', 'Order #')}</th>
                      <th className="p-3">{fa('خریدار', 'Buyer')}</th>
                      <th className="p-3">{fa('فروشنده', 'Seller')}</th>
                      <th className="p-3">{fa('مبلغ', 'Amount')}</th>
                      <th className="p-3">{fa('وضعیت', 'Status')}</th>
                      <th className="p-3">{fa('پرداخت', 'Payment')}</th>
                      <th className="p-3">{fa('تاریخ', 'Date')}</th>
                      <th className="p-3">{fa('عملیات', 'Actions')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredOrders.length === 0 ? (
                      <tr><td colSpan={8} className="p-6 text-center text-[var(--color-night-200)]/50">{fa('سفارشی یافت نشد', 'No orders found')}</td></tr>
                    ) : filteredOrders.map((order) => (
                      <tr key={order.id} className="border-t border-white/5 hover:bg-white/5">
                        <td className="text-right p-3 font-mono text-xs text-[var(--color-night-100)]">{order.order_number}</td>
                        <td className="p-3 text-[var(--color-night-200)]/70 text-xs">{order.buyer_id.slice(0, 8)}...</td>
                        <td className="p-3 text-[var(--color-night-200)]/70 text-xs">{order.seller_id ? order.seller_id.slice(0, 8) + '...' : '-'}</td>
                        <td className="p-3 font-bold text-[var(--color-night-100)]">{Number(order.total).toLocaleString()} {order.currency}</td>
                        <td className="p-3">
                          <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${statusColors[STATUS_LABELS[order.status]?.color] || 'bg-gray-500/20 text-gray-400'}`}>
                            {fa === 'fa' ? STATUS_LABELS[order.status].fa : STATUS_LABELS[order.status].en}
                          </span>
                        </td>
                        <td className="p-3">
                          <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${paymentStatusColors[PAYMENT_STATUS_LABELS[order.payment_status]?.color] || 'bg-gray-500/20 text-gray-400'}`}>
                            {fa === 'fa' ? PAYMENT_STATUS_LABELS[order.payment_status].fa : PAYMENT_STATUS_LABELS[order.payment_status].en}
                          </span>
                        </td>
                        <td className="p-3 text-xs text-[var(--color-night-200)]/60">{new Date(order.created_at).toLocaleDateString()}</td>
                        <td className="p-3">
                          <div className="flex items-center gap-2">
                            <button className="text-[var(--color-night-200)]/50 hover:text-[var(--color-leaf-400)] transition" title={fa('مشاهده', 'View')}>
                              <Eye className="h-4 w-4" />
                            </button>
                            <div className="relative">
                              <button className="text-[var(--color-night-200)]/50 hover:text-[var(--color-leaf-400)] transition" title={fa('اقدامات', 'Actions')}>
                                <MoreVertical className="h-4 w-4" />
                              </button>
                            </div>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="px-4 py-4 border-t border-white/10 flex items-center justify-between">
                  <p className="text-sm text-[var(--color-night-200)]/60">
                    {fa('صفحه', 'Page')} {page} {fa('از', 'of')} {totalPages} ({totalCount} {fa('سفارش', 'orders')})
                  </p>
                  <div className="flex items-center gap-2">
                    <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="p-2 rounded-lg bg-[var(--color-night-50)] hover:bg-[var(--color-leaf-500)]/10 text-[var(--color-night-200)]/60 hover:text-[var(--color-leaf-400)] disabled:opacity-50 disabled:hover:bg-transparent transition"><ChevronRight className="h-4 w-4" /></button>
                    <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="p-2 rounded-lg bg-[var(--color-night-50)] hover:bg-[var(--color-leaf-500)]/10 text-[var(--color-night-200)]/60 hover:text-[var(--color-leaf-400)] disabled:opacity-50 disabled:hover:bg-transparent transition"><ChevronLeft className="h-4 w-4" /></button>
                  </div>
                </div>
              )}
            </div>
          </Reveal>
        </div>
      </div>
    </>
  );
}