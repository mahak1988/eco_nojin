import { useState, useEffect } from 'react';
import { useBilingual } from '../../hooks/useBilingual';
import { adminStats, adminApproveProduct, adminApproveVendor } from '../../lib/marketplaceApi';
import { useAuth } from '../../context/AuthContext';
import Seo from '../../components/ui/Seo';
import Reveal from '../../components/ui/Reveal';
import { Shield, Package, Users, BarChart3, Check, X, Loader2, AlertTriangle } from 'lucide-react';
import type { Product } from '../../lib/marketplaceTypes';

interface Vendor {
  id: string;
  shop_name: string;
  status: 'pending' | 'active' | 'suspended';
  created_at: string;
}

interface AdminStats {
  total_products: number;
  total_producers: number;
  organic_products: number;
  orders: Record<string, unknown>;
}

type Tab = 'products' | 'vendors' | 'orders';

export default function AdminPanel() {
  const { fa, isFa } = useBilingual();
  const { user, isLoading: authLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<Tab>('products');
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes] = await Promise.all([
          adminStats(),
          adminStats().then(() => adminStats()),
          adminStats(),
        ]);
        
        setStats(statsRes);
        const prodRes = await fetch(`${(window as any).API_BASE_URL || ''}/api/v1/marketplace/products?limit=100`);
        const prodData = await prodRes.json();
        setProducts(prodData.products || []);
        
        const vendRes = await fetch(`${(window as any).API_BASE_URL || ''}/api/v1/marketplace/vendors`);
        const vendData = await vendRes.json();
        setVendors(vendData.vendors || []);
      } catch (err) {
        console.error('Failed to load admin data:', err);
      } finally {
        setLoading(false);
      }
    };

    if (!authLoading) {
      fetchData();
    }
  }, [authLoading]);

  const handleProductApprove = async (productId: string, approve: boolean) => {
    setActionLoading(`product-${productId}`);
    try {
      await adminApproveProduct(productId, approve);
      setProducts(prev => prev.map(p => p.id === productId ? { ...p, status: approve ? 'approved' : 'rejected' } : p));
    } catch (err) {
      console.error('Failed to update product:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleVendorApprove = async (vendorId: string, approve: boolean) => {
    setActionLoading(`vendor-${vendorId}`);
    try {
      await adminApproveVendor(vendorId, approve);
      setVendors(prev => prev.map(v => v.id === vendorId ? { ...v, status: approve ? 'active' : 'suspended' } : v));
    } catch (err) {
      console.error('Failed to update vendor:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { bg: string; text: string; label: string }> = {
      pending: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: fa('در انتظار', 'Pending') },
      approved: { bg: 'bg-green-100', text: 'text-green-800', label: fa('تأیید شده', 'Approved') },
      rejected: { bg: 'bg-red-100', text: 'text-red-800', label: fa('رد شده', 'Rejected') },
      out_of_stock: { bg: 'bg-gray-100', text: 'text-gray-800', label: fa('ناموجود', 'Out of Stock') },
      active: { bg: 'bg-green-100', text: 'text-green-800', label: fa('فعال', 'Active') },
      suspended: { bg: 'bg-red-100', text: 'text-red-800', label: fa('معلق', 'Suspended') },
    };
    const v = variants[status] || variants.pending;
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${v.bg} ${v.text}`}>
        {v.label}
      </span>
    );
  };

  const statCards = [
    { icon: Package, label: fa('کل محصولات', 'Total Products'), value: stats?.total_products ?? 0 },
    { icon: Users, label: fa('کل تولیدکنندگان', 'Total Producers'), value: stats?.total_producers ?? 0 },
    { icon: Shield, label: fa('محصولات ارگانیک', 'Organic Products'), value: stats?.organic_products ?? 0 },
    { icon: BarChart3, label: fa('درآمد', 'Revenue'), value: fa('—', '—') },
  ];

  if (authLoading) {
    return (
      <>
        <Seo title="پنل ادمین" path="/marketplace/admin" />
        <div className="min-h-screen bg-[var(--color-sand-50)] flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-[var(--color-gold-500)]" aria-hidden />
        </div>
      </>
    );
  }

  if (!user?.is_admin) {
    return (
      <>
        <Seo title="پنل ادمین" path="/marketplace/admin" />
        <div className="min-h-screen bg-[var(--color-sand-50)] flex items-center justify-center">
          <Reveal className="text-center p-8">
            <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" aria-hidden />
            <h1 className="text-2xl font-bold text-[var(--color-night-100)] mb-2">
              {fa('دسترسی محدود است', 'Access Denied')}
            </h1>
            <p className="text-[var(--color-night-200)]">
              {fa('فقط مدیران می‌توانند به این صفحه دسترسی داشته باشند.', 'Only administrators can access this page.')}
            </p>
          </Reveal>
        </div>
      </>
    );
  }

  return (
    <>
      <Seo title="پنل ادمین" path="/marketplace/admin" />
      <div className="min-h-screen bg-[var(--color-sand-50)]">
        <div className="px-4 py-8 sm:px-6 lg:px-8">
          <Reveal className="mx-auto max-w-7xl space-y-8">
            <header>
              <h1 className="text-3xl font-bold text-[var(--color-night-100)]">
                {fa('پنل ادمین', 'Admin Panel')}
              </h1>
              <p className="mt-1 text-[var(--color-night-200)]">
                {fa('مدیریت بازارگاه و تأیید محصولات و فروشندگان', 'Manage marketplace and approve products and vendors')}
              </p>
            </header>

            {loading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-[var(--color-gold-500)]" aria-hidden />
              </div>
            ) : (
              <>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  {statCards.map((stat, index) => (
                    <Reveal key={index} delay={index * 0.1} className="bg-white rounded-2xl border border-[var(--color-sand-200)] p-6">
                      <div className="flex items-center gap-4">
                        <div className="p-3 bg-[var(--color-sand-100)] rounded-xl">
                          <stat.icon className="w-6 h-6 text-[var(--color-gold-500)]" aria-hidden />
                        </div>
                        <div>
                          <p className="text-sm text-[var(--color-night-200)]">{stat.label}</p>
                          <p className="text-2xl font-bold text-[var(--color-night-100)]">
                            {typeof stat.value === 'number' ? stat.value.toLocaleString(isFa ? 'fa-IR' : 'en-US') : stat.value}
                          </p>
                        </div>
                      </div>
                    </Reveal>
                  ))}
                </div>

                <div className="bg-white rounded-2xl border border-[var(--color-sand-200)] overflow-hidden">
                  <nav className="flex border-b border-[var(--color-sand-200)]" role="tablist">
                    {(['products', 'vendors', 'orders'] as Tab[]).map((tab) => (
                      <button
                        key={tab}
                        role="tab"
                        aria-selected={activeTab === tab}
                        onClick={() => setActiveTab(tab)}
                        className={`px-6 py-4 text-sm font-medium transition-colors border-b-2 -mb-px ${
                          activeTab === tab
                            ? 'border-[var(--color-gold-500)] text-[var(--color-gold-500)]'
                            : 'border-transparent text-[var(--color-night-200)] hover:text-[var(--color-night-100)]'
                        }`}
                      >
                        {tab === 'products' && fa('محصولات', 'Products')}
                        {tab === 'vendors' && fa('فروشندگان', 'Vendors')}
                        {tab === 'orders' && fa('سفارش‌ها', 'Orders')}
                      </button>
                    ))}
                  </nav>

                  <div className="p-6">
                    {activeTab === 'products' && (
                      <div className="space-y-4">
                        <h2 className="text-lg font-semibold text-[var(--color-night-100)]">
                          {fa('لیست محصولات', 'Products List')} ({products.length})
                        </h2>
                        {products.length === 0 ? (
                          <p className="text-[var(--color-night-200)] text-center py-8">
                            {fa('محصولی یافت نشد', 'No products found')}
                          </p>
                        ) : (
                          <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                              <thead>
                                <tr className="text-right border-b border-[var(--color-sand-200)]">
                                  <th className="pb-3 font-medium text-[var(--color-night-200)]">
                                    {fa('نام', 'Name')}
                                  </th>
                                  <th className="pb-3 font-medium text-[var(--color-night-200)]">
                                    {fa('دسته‌بندی', 'Category')}
                                  </th>
                                  <th className="pb-3 font-medium text-[var(--color-night-200)]">
                                    {fa('وضعیت', 'Status')}
                                  </th>
                                  <th className="pb-3 font-medium text-[var(--color-night-200)]">
                                    {fa('قیمت', 'Price')}
                                  </th>
                                  <th className="pb-3 font-medium text-[var(--color-night-200)]">
                                    {fa('عملیات', 'Actions')}
                                  </th>
                                </tr>
                              </thead>
                              <tbody>
                                {products.map((product) => (
                                  <tr key={product.id} className="border-b border-[var(--color-sand-100)]">
                                    <td className="py-4 font-medium text-[var(--color-night-100)]">
                                      {product.name}
                                    </td>
                                    <td className="py-4 text-[var(--color-night-200)]">
                                      {product.category}
                                    </td>
                                    <td className="py-4">
                                      {getStatusBadge(product.status)}
                                    </td>
                                    <td className="py-4 text-[var(--color-night-100)]">
                                      {product.price.toLocaleString(isFa ? 'fa-IR' : 'en-US')} {fa('ریال', 'IRR')}
                                    </td>
                                    <td className="py-4">
                                      <div className="flex items-center gap-2 justify-end">
                                        {product.status === 'pending' && (
                                          <>
                                            <button
                                              onClick={() => handleProductApprove(product.id, true)}
                                              disabled={actionLoading === `product-${product.id}`}
                                              className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                                              title={fa('تأیید', 'Approve')}
                                            >
                                              {actionLoading === `product-${product.id}` ? (
                                                <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
                                              ) : (
                                                <Check className="w-4 h-4" aria-hidden />
                                              )}
                                            </button>
                                            <button
                                              onClick={() => handleProductApprove(product.id, false)}
                                              disabled={actionLoading === `product-${product.id}`}
                                              className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                              title={fa('رد', 'Reject')}
                                            >
                                              {actionLoading === `product-${product.id}` ? (
                                                <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
                                              ) : (
                                                <X className="w-4 h-4" aria-hidden />
                                              )}
                                            </button>
                                          </>
                                        )}
                                        {product.status !== 'pending' && (
                                          <span className="text-[var(--color-night-200)] text-xs">
                                            {fa('پردازش شده', 'Processed')}
                                          </span>
                                        )}
                                      </div>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    )}

                    {activeTab === 'vendors' && (
                      <div className="space-y-4">
                        <h2 className="text-lg font-semibold text-[var(--color-night-100)]">
                          {fa('لیست فروشندگان', 'Vendors List')} ({vendors.length})
                        </h2>
                        {vendors.length === 0 ? (
                          <p className="text-[var(--color-night-200)] text-center py-8">
                            {fa('فروشنده‌ای یافت نشد', 'No vendors found')}
                          </p>
                        ) : (
                          <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                              <thead>
                                <tr className="text-right border-b border-[var(--color-sand-200)]">
                                  <th className="pb-3 font-medium text-[var(--color-night-200)]">
                                    {fa('نام فروشگاه', 'Shop Name')}
                                  </th>
                                  <th className="pb-3 font-medium text-[var(--color-night-200)]">
                                    {fa('وضعیت', 'Status')}
                                  </th>
                                  <th className="pb-3 font-medium text-[var(--color-night-200)]">
                                    {fa('تاریخ ثبت', 'Registered')}
                                  </th>
                                  <th className="pb-3 font-medium text-[var(--color-night-200)]">
                                    {fa('عملیات', 'Actions')}
                                  </th>
                                </tr>
                              </thead>
                              <tbody>
                                {vendors.map((vendor) => (
                                  <tr key={vendor.id} className="border-b border-[var(--color-sand-100)]">
                                    <td className="py-4 font-medium text-[var(--color-night-100)]">
                                      {vendor.shop_name}
                                    </td>
                                    <td className="py-4">
                                      {getStatusBadge(vendor.status)}
                                    </td>
                                    <td className="py-4 text-[var(--color-night-200)]">
                                      {new Date(vendor.created_at).toLocaleDateString(isFa ? 'fa-IR' : 'en-US')}
                                    </td>
                                    <td className="py-4">
                                      <div className="flex items-center gap-2 justify-end">
                                        {vendor.status === 'pending' && (
                                          <>
                                            <button
                                              onClick={() => handleVendorApprove(vendor.id, true)}
                                              disabled={actionLoading === `vendor-${vendor.id}`}
                                              className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                                              title={fa('تأیید', 'Approve')}
                                            >
                                              {actionLoading === `vendor-${vendor.id}` ? (
                                                <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
                                              ) : (
                                                <Check className="w-4 h-4" aria-hidden />
                                              )}
                                            </button>
                                            <button
                                              onClick={() => handleVendorApprove(vendor.id, false)}
                                              disabled={actionLoading === `vendor-${vendor.id}`}
                                              className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                              title={fa('رد', 'Reject')}
                                            >
                                              {actionLoading === `vendor-${vendor.id}` ? (
                                                <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
                                              ) : (
                                                <X className="w-4 h-4" aria-hidden />
                                              )}
                                            </button>
                                          </>
                                        )}
                                        {vendor.status !== 'pending' && (
                                          <span className="text-[var(--color-night-200)] text-xs">
                                            {fa('پردازش شده', 'Processed')}
                                          </span>
                                        )}
                                      </div>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    )}

                    {activeTab === 'orders' && (
                      <Reveal className="text-center py-12">
                        <Package className="w-12 h-12 text-[var(--color-sand-300)] mx-auto mb-4" aria-hidden />
                        <h3 className="text-lg font-medium text-[var(--color-night-100)] mb-2">
                          {fa('در حال توسعه', 'Under Development')}
                        </h3>
                        <p className="text-[var(--color-night-200)]">
                          {fa('مدیریت سفارش‌ها به زودی اضافه خواهد شد.', 'Order management coming soon.')}
                        </p>
                      </Reveal>
                    )}
                  </div>
                </div>
              </>
            )}
          </Reveal>
        </div>
      </div>
    </>
  );
}