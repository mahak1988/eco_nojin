/** Commerce Shipping - Order fulfillment and tracking */

import { useState, useEffect } from 'react';
import { useBilingual } from '../../../hooks/useBilingual';
import { fetchOrders, shipOrder, markDelivered } from '../../../lib/commerceApi';
import type { Order, OrderStatus } from '../../../lib/commerceTypes';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { Truck, CheckCircle2, Loader2, Search, Filter, MapPin, Clock, Package, AlertCircle } from 'lucide-react';

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

const statusColors: Record<string, string> = {
  green: 'bg-[var(--color-leaf-500)]/20 text-[var(--color-leaf-400)]',
  yellow: 'bg-[#e8c66b]/20 text-[#e8c66b]',
  blue: 'bg-[var(--color-aqua-500)]/20 text-[var(--color-aqua-400)]',
  purple: 'bg-purple-500/20 text-purple-400',
  red: 'bg-red-500/20 text-red-400',
  orange: 'bg-orange-500/20 text-orange-400',
  gray: 'bg-gray-500/20 text-gray-400',
};

const SHIPPING_STATUSES: OrderStatus[] = ['paid', 'processing', 'shipped', 'delivered'];

export default function CommerceShippingPage() {
  const { fa } = useBilingual();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [trackingCodes, setTrackingCodes] = useState<Record<string, string>>({});

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchOrders({ limit: 50 });
      setOrders(res.orders.filter(o => SHIPPING_STATUSES.includes(o.status)));
    } catch (err: any) {
      setError(err.message || fa('خطا در بارگذاری', 'Failed to load'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleShip = async (orderId: string, trackingCode: string) => {
    if (!trackingCode.trim()) return;
    setActionLoading(orderId);
    try {
      await shipOrder(orderId, trackingCode);
      loadData();
      setTrackingCodes(prev => ({ ...prev, [orderId]: '' }));
    } catch (err: any) {
      alert(fa('خطا: ' + (err.message || 'نامشخص'), 'Error: ' + (err.message || 'Unknown')));
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeliver = async (orderId: string) => {
    setActionLoading(orderId);
    try {
      await markDelivered(orderId);
      loadData();
    } catch (err: any) {
      alert(fa('خطا: ' + (err.message || 'نامشخص'), 'Error: ' + (err.message || 'Unknown')));
    } finally {
      setActionLoading(null);
    }
  };

  const shippingOrders = orders.filter(o => ['paid', 'processing', 'shipped'].includes(o.status));
  const pendingShip = orders.filter(o => o.status === 'paid' || o.status === 'processing').length;
  const inTransit = orders.filter(o => o.status === 'shipped').length;
  const deliveredCount = orders.filter(o => o.status === 'delivered').length;

  const statusColors: Record<string, string> = {
    green: 'bg-[var(--color-leaf-500)]/20 text-[var(--color-leaf-400)]',
    yellow: 'bg-[#e8c66b]/20 text-[#e8c66b]',
    blue: 'bg-[var(--color-aqua-500)]/20 text-[var(--color-aqua-400)]',
    purple: 'bg-purple-500/20 text-purple-400',
    red: 'bg-red-500/20 text-red-400',
    orange: 'bg-orange-500/20 text-orange-400',
    gray: 'bg-gray-500/20 text-gray-400',
  };

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-[var(--color-leaf-400)]" /></div>;
  if (error) return <div className="p-6 text-center text-red-400">{error}</div>;

  return (
    <>
      <Seo title={fa('مدیریت حمل و نقل', 'Shipping Management')} path="/dashboard/commerce/shipping" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-7xl">
          <h1 className="mb-6 text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
            <Truck className="h-6 w-6 text-[var(--color-leaf-400)]" />
            {fa('مدیریت حمل و نقل', 'Shipping Management')}
          </h1>

          {/* Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <Reveal delay={0}><div className="glass rounded-2xl p-4 text-center"><p className="text-3xl font-extrabold text-[#e8c66b]">{pendingShip}</p><p className="text-xs text-[var(--color-night-200)]/60">{fa('آماده ارسال', 'Ready to Ship')}</p></div></Reveal>
            <Reveal delay={0.07}><div className="glass rounded-2xl p-4 text-center"><p className="text-3xl font-extrabold text-[var(--color-aqua-400)]">{inTransit}</p><p className="text-xs text-[var(--color-night-200)]/60">{fa('در حال حمل', 'In Transit')}</p></div></Reveal>
            <Reveal delay={0.14}><div className="glass rounded-2xl p-4 text-center"><p className="text-3xl font-extrabold text-[var(--color-leaf-400)]">{deliveredCount}</p><p className="text-xs text-[var(--color-night-200)]/60">{fa('تحویل داده شده', 'Delivered')}</p></div></Reveal>
            <Reveal delay={0.21}><div className="glass rounded-2xl p-4 text-center"><p className="text-3xl font-extrabold text-[var(--color-night-100)]">{orders.length}</p><p className="text-xs text-[var(--color-night-200)]/60">{fa('کل حمل‌ها', 'Total Shipments')}</p></div></Reveal>
          </div>

          {/* Shipping Table */}
          <Reveal delay={0.3}>
            <div className="glass rounded-2xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm" dir="ltr">
                  <thead className="bg-[#f6ecd6]"><tr className="text-[var(--color-night-200)]/60 text-[11px] uppercase">
                    <th className="text-right p-3">{fa('سفارش', 'Order')}</th>
                    <th className="p-3">{fa('فروشنده', 'Seller')}</th>
                    <th className="p-3">{fa('مبلغ', 'Amount')}</th>
                    <th className="p-3">{fa('وضعیت', 'Status')}</th>
                    <th className="p-3">{fa('کد رهگیری', 'Tracking')}</th>
                    <th className="p-3">{fa('آدرس مقصد', 'Destination')}</th>
                    <th className="p-3">{fa('تاریخ', 'Date')}</th>
                    <th className="p-3">{fa('عملیات', 'Actions')}</th>
                  </tr></thead>
                  <tbody>
                    {orders.length === 0 ? (
                      <tr><td colSpan={8} className="p-6 text-center text-[var(--color-night-200)]/50">{fa('سفارشی برای حمل یافت نشد', 'No orders for shipping')}</td></tr>
                    ) : orders.map((order) => (
                      <tr key={order.id} className="border-t border-white/5">
                        <td className="text-right p-3 font-mono text-xs text-[var(--color-night-100)]">{order.order_number}</td>
                        <td className="p-3 text-[var(--color-night-200)]/70 text-xs">{order.seller_id ? order.seller_id.slice(0, 8) + '...' : '-'}</td>
                        <td className="p-3 font-bold text-[var(--color-night-100)]">{Number(order.total).toLocaleString()} {order.currency}</td>
                        <td className="p-3"><span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${statusColors[STATUS_LABELS[order.status]?.color] || 'bg-gray-500/20 text-gray-400'}`}>{fa === 'fa' ? STATUS_LABELS[order.status].fa : STATUS_LABELS[order.status].en}</span></td>
                        <td className="p-3">
                          {order.tracking_code ? (
                            <span className="font-mono text-xs text-[var(--color-leaf-400)]">{order.tracking_code}</span>
                          ) : (
                            <span className="text-[var(--color-night-200)]/50">{fa('ثبت نشده', 'Not set')}</span>
                          )}
                        </td>
                        <td className="p-3 text-[var(--color-night-200)]/70 text-xs max-w-[200px] truncate">
                          {order.shipping_address ? `${order.shipping_address.city || ''} ${order.shipping_address.address || ''}` : '-'}
                        </td>
                        <td className="p-3 text-xs text-[var(--color-night-200)]/60">{order.shipped_at ? new Date(order.shipped_at).toLocaleDateString() : new Date(order.created_at).toLocaleDateString()}</td>
                        <td className="p-3">
                          <div className="flex items-center gap-2">
                            {(order.status === 'paid' || order.status === 'processing') && (
                              <div className="flex items-center gap-2">
                                <input
                                  type="text"
                                  placeholder={fa('کد رهگیری', 'Tracking code')}
                                  value={trackingCodes[order.id] || ''}
                                  onChange={e => setTrackingCodes(prev => ({ ...prev, [order.id]: e.target.value }))}
                                  className="w-32 px-2 py-1.5 text-xs bg-[var(--color-night-50)] border border-[var(--color-night-200)]/20 rounded-xl text-[var(--color-night-100)] focus:outline-none focus:ring-2 focus:ring-[var(--color-leaf-400)]"
                                />
                                <button
                                  onClick={() => handleShip(order.id, trackingCodes[order.id] || '')}
                                  disabled={!trackingCodes[order.id]?.trim()}
                                  className="flex items-center gap-1.5 rounded-xl bg-[var(--color-aqua-500)] px-3 py-2 text-xs font-extrabold text-white transition hover:bg-[var(--color-aqua-600)] disabled:opacity-50"
                                >
                                  <Truck className="h-3.5 w-3.5" />
                                  {fa('ارسال', 'Ship')}
                                </button>
                              </div>
                            )}
                            {(order.status === 'shipped') && (
                              <button onClick={() => handleDeliver(order.id)} className="flex items-center gap-1.5 rounded-xl bg-[var(--color-leaf-500)] px-3 py-2 text-xs font-extrabold text-white transition hover:bg-[var(--color-leaf-600)]">
                                <CheckCircle2 className="h-3.5 w-3.5" />
                                {fa('تحویل', 'Deliver')}
                              </button>
                            )}
                            {(order.status === 'delivered') && (
                              <span className="flex items-center gap-1 text-[var(--color-leaf-400)] text-xs font-bold"><CheckCircle2 className="h-3.5 w-3.5" /> {fa('تحویل داده شده', 'Delivered')}</span>
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