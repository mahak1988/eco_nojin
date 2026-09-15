import { useState, useEffect } from 'react';
import { useBilingual } from '../../hooks/useBilingual';
import { useAuth } from '../../context/AuthContext';
import { fetchVendorProducts, fetchVendorOrders } from '../../lib/marketplaceApi';
import { ORDER_STATUS_LABEL } from './catalog-shared';
import type { Order, Product } from '../../lib/marketplaceTypes';
import Seo from '../../components/ui/Seo';
import Reveal from '../../components/ui/Reveal';
import { BarChart3, Package, ClipboardList, Check, Loader2, TrendingUp, AlertCircle } from 'lucide-react';

export default function VendorDashboard() {
  const { fa } = useBilingual();
  const { user } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const vendorId = user?.id;

  useEffect(() => {
    if (!vendorId) {
      setLoading(false);
      setError('ورود به سیستم مورد نیاز است');
      return;
    }

    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [productsRes, ordersRes] = await Promise.all([
          fetchVendorProducts(vendorId),
          fetchVendorOrders(vendorId),
        ]);
        setProducts(productsRes.products);
        setOrders(ordersRes.orders);
      } catch (err: any) {
        setError(err.message || 'خطا در بارگذاری داده‌ها');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [vendorId]);

  const stats = {
    total: products.length,
    active: products.filter((p) => p.status === 'approved').length,
    sales: orders.filter((o) => o.status === 'delivered').reduce((s, o) => s + o.total, 0),
    pending: orders.filter((o) => o.status === 'pending' || o.status === 'shipped').length,
  };

  if (loading) {
    return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-leaf-400" /></div>;
  }

  if (error) {
    return (
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-5xl">
          <div className="glass rounded-2xl p-6 flex items-center gap-3">
            <AlertCircle className="h-6 w-6 text-red-400" aria-hidden />
            <p className="text-[var(--color-night-200)]/70">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <Seo title="داشبورد فروشنده" path="/marketplace/sell" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-5xl">
          <h1 className="mb-6 text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2"><Package className="h-6 w-6 text-[var(--color-leaf-400)]" />{fa('داشبورد فروشنده', 'Vendor Dashboard')}</h1>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {[
              { icon: BarChart3, label: fa('محصولات', 'Products'), value: stats.total, color: 'leaf' },
              { icon: Check, label: fa('فعال', 'Active'), value: stats.active, color: 'leaf' },
              { icon: TrendingUp, label: fa('فروش', 'Sales'), value: stats.sales.toLocaleString(), color: 'sand' },
              { icon: ClipboardList, label: fa('در انتظار', 'Pending'), value: stats.pending, color: 'aqua' },
            ].map((s) => (
              <Reveal key={s.label}>
                <div className="glass rounded-2xl p-4 text-center">
                  <s.icon className="h-6 w-6 mx-auto mb-2 text-[var(--color-leaf-400)]" aria-hidden />
                  <p className="text-2xl font-extrabold text-[var(--color-night-100)]">{s.value}</p>
                  <p className="text-xs text-[var(--color-night-200)]/60">{s.label}</p>
                </div>
              </Reveal>
            ))}
          </div>
          <h2 className="mb-3 text-lg font-extrabold text-[var(--color-night-100)]">{fa('محصولات', 'Products')}</h2>
          <div className="glass rounded-2xl overflow-hidden mb-8">
            <table className="w-full text-sm">
              <thead className="bg-white/5"><tr className="text-[var(--color-night-200)]/60 text-[11px] uppercase">
                <th className="text-right p-3">{fa('نام', 'Name')}</th>
                <th className="p-3">{fa('قیمت', 'Price')}</th>
                <th className="p-3">{fa('موجودی', 'Stock')}</th>
                <th className="p-3">{fa('وضعیت', 'Status')}</th>
              </tr></thead>
              <tbody>
                {products.length === 0 ? (
                  <tr><td colSpan={4} className="p-6 text-center text-[var(--color-night-200)]/50">{fa('محصولی یافت نشد', 'No products')}</td></tr>
                ) : products.map((p) => (
                  <tr key={p.id} className="border-t border-white/5">
                    <td className="text-right p-3 text-[var(--color-night-100)] font-bold">{p.name}</td>
                    <td className="p-3 text-[var(--color-night-200)]/60">{p.price.toLocaleString()} IRR</td>
                    <td className="p-3 text-[var(--color-night-200)]/60">{p.quantity_available} kg</td>
                    <td className="p-3">
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${p.status === 'approved' ? 'bg-[var(--color-leaf-500)]/15 text-[var(--color-leaf-300)]' : p.status === 'rejected' ? 'bg-red-400/15 text-red-400' : 'bg-yellow-400/15 text-yellow-400'}`}>{fa({ approved: 'تأیید شده', pending: 'در انتظار', rejected: 'رد شده', out_of_stock: 'ناموجود' }[p.status] || p.status, { approved: 'Active', pending: 'Pending', rejected: 'Rejected', out_of_stock: 'OOS' }[p.status] || p.status)}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <h2 className="mb-3 text-lg font-extrabold text-[var(--color-night-100)]">{fa('سفارشات در انتظار', 'Pending Orders')}</h2>
          <div className="flex flex-col gap-3">
            {orders.filter((o) => o.status === 'pending' || o.status === 'shipped').map((order) => (
              <Reveal key={order.id}>
                <div className="glass rounded-2xl p-4 flex items-center justify-between">
                  <div>
                    <p className="font-extrabold text-[var(--color-night-100)] text-sm">#{order.order_number || order.id}</p>
                    <p className="text-xs text-[var(--color-night-200)]/60">{ORDER_STATUS_LABEL[order.status]?.fa || order.status}</p>
                  </div>
                  <span className="text-sm font-bold text-[var(--color-night-100)]">{order.total.toLocaleString()} IRR</span>
                </div>
              </Reveal>
            ))}
            {orders.filter((o) => o.status === 'pending' || o.status === 'shipped').length === 0 && (
              <p className="text-[var(--color-night-200)]/50">{fa('سفارشی در انتظار نیست', 'No pending orders')}</p>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
