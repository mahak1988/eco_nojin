/** Commerce Dashboard — orders, payments, shipping, settlement management. */

import { useState, useEffect } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useBilingual } from '../../../hooks/useBilingual';
import {
  fetchOrders,
  fetchOrder,
  payOrder,
  confirmPayment,
  shipOrder,
  markDelivered,
  cancelOrder,
  settleOrder,
  getAllowedTransitions,
  fetchSettlements,
} from '../../../lib/commerceApi';
import type { Order, OrderStatus, PaymentStatus, Settlement } from '../../../lib/commerceTypes';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { ShoppingCart, CreditCard, Truck, CheckCircle2, RotateCcw, XCircle, Loader2, AlertCircle, MoreHorizontal, Menu, ChevronDown } from 'lucide-react';

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

export default function CommerceDashboard() {
  const { fa } = useBilingual();
  const { isAdmin } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [settlements, setSettlements] = useState<Settlement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('');

  useEffect(() => {
    loadData();
  }, [filterStatus]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ordersRes, settlementsRes] = await Promise.all([
        fetchOrders(filterStatus ? { status: filterStatus } : { limit: 50 }),
        fetchSettlements(),
      ]);
      setOrders(ordersRes.orders);
      setSettlements(settlementsRes);
    } catch (err: any) {
      setError(err.message || fa('خطا در بارگذاری', 'Failed to load'));
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (
    orderId: string,
    action: 'pay' | 'confirm' | 'ship' | 'deliver' | 'cancel' | 'settle',
    extraData?: { trackingCode?: string; reason?: string }
  ) => {
    setActionLoading(orderId);
    try {
      switch (action) {
        case 'pay':
          await payOrder(orderId, 'wallet');
          break;
        case 'confirm':
          await confirmPayment(orderId);
          break;
        case 'ship':
          if (extraData?.trackingCode) await shipOrder(orderId, extraData.trackingCode);
          break;
        case 'deliver':
          await markDelivered(orderId);
          break;
        case 'cancel':
          if (extraData?.reason) await cancelOrder(orderId, extraData.reason);
          break;
        case 'settle':
          await settleOrder(orderId);
          break;
      }
      loadData();
      if (selectedOrder?.id === orderId) {
        const updated = await fetchOrder(orderId);
        setSelectedOrder(updated);
      }
    } catch (err: any) {
      alert(fa('خطا: ' + (err.message || 'نامشخص'), 'Error: ' + (err.message || 'Unknown')));
    } finally {
      setActionLoading(null);
    }
  };

  const openOrderDetail = async (order: Order) => {
    try {
      const detail = await fetchOrder(order.id);
      setSelectedOrder(detail);
    } catch {
      setSelectedOrder(order);
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

  const filteredOrders = orders.filter(o => !filterStatus || o.status === filterStatus);
  const pendingCount = orders.filter(o => o.status === 'reserved' || o.payment_status === 'pending' || o.payment_status === 'authorized').length;
  const processingCount = orders.filter(o => o.status === 'processing').length;
  const shippedCount = orders.filter(o => o.status === 'shipped').length;

  if (loading) {
    return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-[var(--color-leaf-400)]" /></div>;
  }

  if (error) {
    return (
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-6xl">
          <div className="glass rounded-2xl p-6 flex items-center gap-3">
            <AlertCircle className="h-6 w-6 text-red-400" aria-hidden />
            <p className="text-[var(--color-night-200)]/70">{error}</p>
            <button onClick={loadData} className="ml-auto text-[var(--color-leaf-400)] hover:underline">{fa('تلاش مجدد', 'Retry')}</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <Seo title={fa('داشبورد تجارت', 'Commerce Dashboard')} path="/dashboard/commerce" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-7xl">
          <h1 className="mb-6 text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
            <ShoppingCart className="h-6 w-6 text-[var(--color-leaf-400)]" />
            {fa('داشبورد تجارت', 'Commerce Dashboard')}
          </h1>

          {/* Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-6 gap-4 mb-8">
            <Reveal delay={0}>
              <div className="glass rounded-2xl p-4 text-center">
                <p className="text-3xl font-extrabold text-[var(--color-leaf-400)]">{orders.length}</p>
                <p className="text-xs text-[var(--color-night-200)]/60">{fa('کل سفارشات', 'Total Orders')}</p>
              </div>
            </Reveal>
            <Reveal delay={0.07}>
              <div className="glass rounded-2xl p-4 text-center">
                <p className="text-3xl font-extrabold text-[#e8c66b]">{pendingCount}</p>
                <p className="text-xs text-[var(--color-night-200)]/60">{fa('در انتظار پرداخت/تأیید', 'Awaiting Payment')}</p>
              </div>
            </Reveal>
            <Reveal delay={0.14}>
              <div className="glass rounded-2xl p-4 text-center">
                <p className="text-3xl font-extrabold text-[var(--color-aqua-400)]">{processingCount}</p>
                <p className="text-xs text-[var(--color-night-200)]/60">{fa('در پردازش', 'Processing')}</p>
              </div>
            </Reveal>
            <Reveal delay={0.21}>
              <div className="glass rounded-2xl p-4 text-center">
                <p className="text-3xl font-extrabold text-[var(--color-aqua-400)]">{shippedCount}</p>
                <p className="text-xs text-[var(--color-night-200)]/60">{fa('در حال حمل', 'In Transit')}</p>
              </div>
            </Reveal>
            <Reveal delay={0.28}>
              <div className="glass rounded-2xl p-4 text-center">
                <p className="text-3xl font-extrabold text-purple-400">{settlements.length}</p>
                <p className="text-xs text-[var(--color-night-200)]/60">{fa('تسویه‌ها', 'Settlements')}</p>
              </div>
            </Reveal>
            <Reveal delay={0.35}>
              <div className="glass rounded-2xl p-4 text-center">
                <p className="text-3xl font-extrabold text-[var(--color-night-100)]">
                  {orders.filter(o => o.status === 'delivered' || o.status === 'settled').reduce((s, o) => s + Number(o.total), 0).toLocaleString()}
                </p>
                <p className="text-xs text-[var(--color-night-200)]/60">{fa('مبلغ تسویه‌شده', 'Settled Amount')}</p>
              </div>
            </Reveal>
          </div>

          {/* Filter */}
          <Reveal delay={0.4}>
            <div className="glass rounded-2xl p-4 mb-8 flex flex-wrap items-center gap-4">
              <label className="text-sm font-medium text-[var(--color-night-200)]/80">{fa('فیلتر وضعیت:', 'Filter Status:')}</label>
              <select
                value={filterStatus}
                onChange={e => setFilterStatus(e.target.value)}
                className="bg-[var(--color-night-50)] border border-[var(--color-night-200)]/20 rounded-xl px-4 py-2 text-sm text-[var(--color-night-100)] focus:outline-none focus:ring-2 focus:ring-[var(--color-leaf-400)]"
              >
                <option value="">{fa('همه', 'All')}</option>
                <option value="draft">{fa('پیش‌نویس', 'Draft')}</option>
                <option value="reserved">{fa('رزرو شده', 'Reserved')}</option>
                <option value="paid">{fa('پرداخت شده', 'Paid')}</option>
                <option value="processing">{fa('در پردازش', 'Processing')}</option>
                <option value="shipped">{fa('ارسال شده', 'Shipped')}</option>
                <option value="delivered">{fa('تحویل داده شده', 'Delivered')}</option>
                <option value="settled">{fa('تسویه شده', 'Settled')}</option>
                <option value="cancelled">{fa('لغو شده', 'Cancelled')}</option>
                <option value="refunded">{fa('بازپرداخت شده', 'Refunded')}</option>
              </select>
            </div>
          </Reveal>

          {/* Orders Table */}
          <Reveal delay={0.5}>
            <div className="glass rounded-2xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm" dir="ltr">
                  <thead className="bg-[#f6ecd6]">
                    <tr className="text-[var(--color-night-200)]/60 text-[11px] uppercase">
                      <th className="text-right p-3">{fa('شماره سفارش', 'Order #')}</th>
                      <th className="p-3">{fa('خریدار/فروشنده', 'Party')}</th>
                      <th className="p-3">{fa('مبلغ', 'Amount')}</th>
                      <th className="p-3">{fa('وضعیت', 'Status')}</th>
                      <th className="p-3">{fa('پرداخت', 'Payment')}</th>
                      <th className="p-3">{fa('تاریخ', 'Date')}</th>
                      <th className="p-3">{fa('عملیات', 'Actions')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredOrders.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="p-6 text-center text-[var(--color-night-200)]/50">
                          {fa('سفارشی یافت نشد', 'No orders found')}
                        </td>
                      </tr>
                    ) : filteredOrders.map((order) => (
                      <tr key={order.id} className="border-t border-white/5 hover:bg-white/5 cursor-pointer" onClick={() => openOrderDetail(order)}>
                        <td className="text-right p-3 font-mono text-xs text-[var(--color-night-100)]">{order.order_number.slice(0, 20)}</td>
                        <td className="p-3 text-[var(--color-night-200)]/70 text-xs">
                          {fa('خریدار', 'Buyer')}: {order.buyer_id.slice(0, 8)}...
                          {order.seller_id && <span className="block mt-1">{fa('فروشنده', 'Seller')}: {order.seller_id.slice(0, 8)}...</span>}
                        </td>
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
                          <button
                            onClick={e => { e.stopPropagation(); openOrderDetail(order); }}
                            className="text-[var(--color-night-200)]/50 hover:text-[var(--color-leaf-400)] transition"
                            aria-label={fa('مشاهده جزئیات', 'View Details')}
                          >
                            <MoreHorizontal className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </Reveal>

          {/* Settlements */}
          {settlements.length > 0 && (
            <Reveal delay={0.6}>
              <div className="glass rounded-2xl p-6 mt-8">
                <h3 className="flex items-center gap-2 text-base font-extrabold text-[var(--color-night-100)] mb-4">
                  <CheckCircle2 className="h-5 w-5 text-purple-400" />
                  {fa('تسویه‌های اخیر', 'Recent Settlements')}
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm" dir="ltr">
                    <thead>
                      <tr className="text-xs text-[var(--color-night-200)]/60 text-left">
                        <th className="pb-2">{fa('شناسه', 'ID')}</th>
                        <th className="pb-2">{fa('سفارش', 'Order')}</th>
                        <th className="pb-2">{fa('فروشنده', 'Seller')}</th>
                        <th className="pb-2">{fa('مبلغ', 'Amount')}</th>
                        <th className="pb-2">{fa('وضعیت', 'Status')}</th>
                        <th className="pb-2">{fa('تاریخ', 'Date')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {settlements.slice(0, 10).map((s) => (
                        <tr key={s.id} className="border-t border-white/5">
                          <td className="py-2 font-mono text-xs">{s.id.slice(0, 16)}</td>
                          <td className="py-2 font-mono text-xs">{s.order_id.slice(0, 16)}</td>
                          <td className="py-2 text-[var(--color-night-200)]/70">{s.seller_id.slice(0, 8)}...</td>
                          <td className="py-2 font-bold">{Number(s.amount).toLocaleString()} {s.currency}</td>
                          <td className="py-2">
                            <span className="rounded-full px-2 py-0.5 text-xs bg-purple-500/20 text-purple-400">{s.status}</span>
                          </td>
                          <td className="py-2 text-xs">{new Date(s.created_at).toLocaleDateString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </Reveal>
          )}

          {/* Order Detail Modal */}
          {selectedOrder && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={() => setSelectedOrder(null)}>
              <div className="glass rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
                <div className="p-6 border-b border-white/10 flex items-center justify-between">
                  <h3 className="text-lg font-extrabold text-[var(--color-night-100)]">
                    {fa('جزئیات سفارش', 'Order Details')} - {selectedOrder.order_number}
                  </h3>
                  <button onClick={() => setSelectedOrder(null)} className="text-[var(--color-night-200)]/60 hover:text-[var(--color-night-100)]">
                    <XCircle className="h-5 w-5" />
                  </button>
                </div>
                <div className="p-6 space-y-6">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div><span className="text-[var(--color-night-200)]/60">{fa('شناسه', 'ID')}</span> <p className="font-mono text-xs">{selectedOrder.id}</p></div>
                    <div><span className="text-[var(--color-night-200)]/60">{fa('شماره سفارش', 'Order #')}</span> <p className="font-mono text-xs">{selectedOrder.order_number}</p></div>
                    <div><span className="text-[var(--color-night-200)]/60">{fa('وضعیت', 'Status')}</span>
                      <p><span className={`rounded-full px-2 py-0.5 text-xs ${statusColors[STATUS_LABELS[selectedOrder.status]?.color]}`}>{fa === 'fa' ? STATUS_LABELS[selectedOrder.status].fa : STATUS_LABELS[selectedOrder.status].en}</span></p>
                    </div>
                    <div><span className="text-[var(--color-night-200)]/60">{fa('پرداخت', 'Payment')}</span>
                      <p><span className={`rounded-full px-2 py-0.5 text-xs ${paymentStatusColors[PAYMENT_STATUS_LABELS[selectedOrder.payment_status]?.color]}`}>{fa === 'fa' ? PAYMENT_STATUS_LABELS[selectedOrder.payment_status].fa : PAYMENT_STATUS_LABELS[selectedOrder.payment_status].en}</span></p>
                    </div>
                    <div><span className="text-[var(--color-night-200)]/60">{fa('مبلغ', 'Amount')}</span> <p className="font-bold">{Number(selectedOrder.total).toLocaleString()} {selectedOrder.currency}</p></div>
                    <div><span className="text-[var(--color-night-200)]/60">{fa('تاریخ', 'Date')}</span> <p>{new Date(selectedOrder.created_at).toLocaleDateString()}</p></div>
                  </div>

                  <div>
                    <h4 className="font-bold text-[var(--color-night-100)] mb-2">{fa('اقلام', 'Items')}</h4>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm" dir="ltr">
                        <thead><tr className="text-xs text-[var(--color-night-200)]/60 text-left"><th className="pb-2">{fa('محصول', 'Product')}</th><th className="pb-2">{fa('تعداد', 'Qty')}</th><th className="pb-2">{fa('قیمت واحد', 'Unit Price')}</th><th className="pb-2">{fa('مجموع', 'Total')}</th></tr></thead>
                        <tbody>
                          {selectedOrder.items.map((item) => (
                            <tr key={item.id} className="border-t border-white/5">
                              <td className="py-2 text-right">{item.name}</td>
                              <td className="py-2">{item.quantity}</td>
                              <td className="py-2">{Number(item.unit_price).toLocaleString()} {selectedOrder.currency}</td>
                              <td className="py-2 font-bold">{Number(item.line_total).toLocaleString()} {selectedOrder.currency}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {selectedOrder.shipping_address && (
                    <div>
                      <h4 className="font-bold text-[var(--color-night-100)] mb-2">{fa('آدرس ارسال', 'Shipping Address')}</h4>
                      <pre className="text-xs text-[var(--color-night-200)]/70 bg-[var(--color-night-50)] p-3 rounded-lg overflow-auto">{JSON.stringify(selectedOrder.shipping_address, null, 2)}</pre>
                    </div>
                  )}

                  <div className="flex flex-wrap gap-3 pt-4 border-t border-white/10">
                    {(() => {
                      const transitions: Array<{ action: 'pay' | 'confirm' | 'ship' | 'deliver' | 'cancel' | 'settle'; label: string; icon: any; disabled: boolean; color: string }> = [
                        { action: 'pay', label: fa('پرداخت', 'Pay'), icon: CreditCard, disabled: selectedOrder.payment_status === 'paid' || selectedOrder.status === 'cancelled', color: 'bg-[var(--color-leaf-500)]' },
                        { action: 'confirm', label: fa('تأیید پرداخت', 'Confirm Payment'), icon: CheckCircle2, disabled: selectedOrder.payment_status !== 'authorized', color: 'bg-[var(--color-aqua-500)]' },
                        { action: 'ship', label: fa('ارسال', 'Ship'), icon: Truck, disabled: selectedOrder.status !== 'paid' && selectedOrder.status !== 'processing', color: 'bg-blue-500' },
                        { action: 'deliver', label: fa('تحویل', 'Deliver'), icon: CheckCircle2, disabled: selectedOrder.status !== 'shipped', color: 'bg-purple-500' },
                        { action: 'settle', label: fa('تسویه', 'Settle'), icon: RotateCcw, disabled: selectedOrder.status !== 'delivered', color: 'bg-purple-600' },
                        { action: 'cancel', label: fa('لغو', 'Cancel'), icon: XCircle, disabled: ['delivered', 'settled', 'cancelled'].includes(selectedOrder.status), color: 'bg-red-500' },
                      ];
                      return transitions.map(t => (
                        <button
                          key={t.action}
                          onClick={async () => {
                            if (t.action === 'ship') {
                              const code = prompt(fa('کد رهگیری را وارد کنید:', 'Enter tracking code:'));
                              if (code) handleAction(selectedOrder.id, t.action, { trackingCode: code });
                            } else if (t.action === 'cancel') {
                              const reason = prompt(fa('دلیل لغو:', 'Cancel reason:'));
                              if (reason) handleAction(selectedOrder.id, t.action, { reason });
                            } else {
                              handleAction(selectedOrder.id, t.action);
                            }
                          }}
                          disabled={t.disabled || actionLoading === selectedOrder.id}
                          className={`flex-1 min-w-[100px] ${t.disabled ? 'opacity-50 cursor-not-allowed' : ''} ${t.color} text-white px-3 py-2 rounded-xl text-xs font-bold transition`}
                        >
                          {actionLoading === selectedOrder.id ? <Loader2 className="h-3.5 w-3.5 animate-spin inline-block ml-1" /> : t.icon}
                          {t.label}
                        </button>
                      ));
                    })()}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}