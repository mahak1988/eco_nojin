import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useBilingual } from '../../hooks/useBilingual';
import { fetchVendor, fetchVendorProducts } from '../../lib/marketplaceApi';
import ProductCard from './ProductCard';
import type { Vendor } from '../../lib/marketplaceTypes';
import Seo from '../../components/ui/Seo';
import PageHeader from '../../components/sections/PageHeader';
import { Star, Check, Loader2 } from 'lucide-react';

export default function VendorPage() {
  const { id } = useParams<{ id: string }>();
  const { fa } = useBilingual();
  const [vendor, setVendor] = useState<Vendor | null>(null);
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    fetchVendor(id).then((v) => {
      setVendor(v);
      return fetchVendorProducts(id);
    }).then((p) => { setProducts(p.products); setLoading(false); }).catch(() => setLoading(false));
  }, [id]);

  if (loading) {
    return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-leaf-400" /></div>;
  }

  if (!vendor) {
    return <div className="text-center py-20 text-[var(--color-night-200)]/60">{fa('فروشنده یافت نشد', 'Vendor not found')}</div>;
  }

  return (
    <>
      <Seo title={vendor.shop_name} path={`/marketplace/vendor/${vendor.id}`} />
      <PageHeader kicker="فروشنده" title={vendor.shop_name} lead={vendor.description} />
      <section className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-6xl flex flex-col gap-8">
          <div className="glass rounded-3xl p-6">
            <div className="flex items-center gap-4">
              <div className="h-16 w-16 rounded-2xl bg-[var(--color-leaf-500)]/15 flex items-center justify-center">
                <span className="text-3xl">🏪</span>
              </div>
              <div className="flex-1">
                <h2 className="text-lg font-extrabold text-[var(--color-night-100)]">{vendor.shop_name}</h2>
                <p className="text-sm text-[var(--color-night-200)]/60">{vendor.location}</p>
                <div className="mt-1 flex items-center gap-3">
                  {vendor.is_verified && <span className="inline-flex items-center gap-1 rounded-full bg-[var(--color-leaf-500)]/15 px-2 py-0.5 text-[10px] font-bold text-[var(--color-leaf-300)]"><Check className="h-3 w-3" />{fa('تأیید شده', 'Verified')}</span>}
                  <span className="inline-flex items-center gap-1 text-xs text-[var(--color-night-200)]/60"><Star className="h-3 w-3 fill-[var(--color-sand-400)] text-[var(--color-sand-400)]" />{vendor.rating}</span>
                </div>
              </div>
            </div>
          </div>
          <h3 className="text-lg font-extrabold text-[var(--color-night-100)]">{fa('محصولات', 'Products')}</h3>
          {products.length === 0 ? (
            <p className="text-[var(--color-night-200)]/60">{fa('محصولی یافت نشد', 'No products')}</p>
          ) : (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
              {products.map((p: any) => (
                <ProductCard key={p.id} product={p} />
              ))}
            </div>
          )}
        </div>
      </section>
    </>
  );
}
