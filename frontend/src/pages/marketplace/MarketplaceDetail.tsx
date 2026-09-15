import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useBilingual } from '../../hooks/useBilingual';
import { fetchMarketplace, fetchMarketplaceShops } from '../../lib/marketplaceApi';
import type { Marketplace } from '../../lib/marketplaceTypes';
import Seo from '../../components/ui/Seo';
import PageHeader from '../../components/sections/PageHeader';
import Reveal from '../../components/ui/Reveal';
import { Loader2, ArrowLeft, Building2, Check, X } from 'lucide-react';

export default function MarketplaceDetail() {
  const { id } = useParams<{ id: string }>();
  const { fa } = useBilingual();
  const [marketplace, setMarketplace] = useState<Marketplace | null>(null);
  const [shops, setShops] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    fetchMarketplace(id).then((m) => {
      setMarketplace(m);
      return fetchMarketplaceShops(id);
    }).then((s) => {
      setShops(s.shops);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="h-10 w-10 animate-spin text-[var(--color-leaf-400)]" />
      </div>
    );
  }

  if (!marketplace) {
    return (
      <div className="text-center py-20">
        <p className="text-[var(--color-night-200)]/60">{fa('بازارچه یافت نشد', 'Marketplace not found')}</p>
        <Link to="/marketplace/directory" className="mt-4 inline-flex items-center gap-2 text-[var(--color-leaf-400)]">
          <ArrowLeft className="h-4 w-4" />{fa('بازگشت', 'Back')}
        </Link>
      </div>
    );
  }

  return (
    <>
      <Seo title={marketplace.name} path={`/marketplace/marketplaces/${marketplace.id}`} />
      <div className="min-h-screen bg-[var(--color-sand-50)]">
        <PageHeader
          kicker={marketplace.marketplace_type === 'rural' ? fa('بازارچه روستایی', 'Rural Marketplace') : fa('بازارچه عشایری', 'Tribal Marketplace')}
          title={marketplace.name}
          lead={marketplace.description || ''}
        />

        <main className="px-4 py-8 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-6xl space-y-12">
            <Reveal>
              <div className="bg-white rounded-3xl border border-[var(--color-sand-200)] overflow-hidden">
                <div className="h-48 bg-gradient-to-br from-[var(--color-leaf-500)]/20 to-[var(--color-night-800)] flex items-center justify-center">
                  {marketplace.banner ? (
                    <img src={marketplace.banner} alt={marketplace.name} className="h-full w-full object-cover" />
                  ) : (
                    <Building2 className="h-16 w-16 text-[var(--color-leaf-400)]/40" aria-hidden />
                  )}
                </div>
                <div className="p-6 sm:p-8">
                  <div className="flex flex-col sm:flex-row items-start justify-between gap-4">
                    <div className="flex items-center gap-4">
                      {marketplace.logo ? (
                        <img src={marketplace.logo} alt={marketplace.name} className="h-16 w-16 rounded-2xl object-cover" />
                      ) : (
                        <div className="h-16 w-16 rounded-2xl bg-[var(--color-leaf-500)]/15 flex items-center justify-center">
                          <Building2 className="h-8 w-8 text-[var(--color-leaf-400)]" aria-hidden />
                        </div>
                      )}
                      <div>
                        <h2 className="text-2xl font-extrabold text-[var(--color-night-100)]">{marketplace.name}</h2>
                        <p className="text-sm text-[var(--color-night-200)]/60">
                          {fa('نوع:', 'Type:')} {marketplace.marketplace_type === 'rural' ? fa('روستایی', 'Rural') : fa('عشایری', 'Tribal')}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {marketplace.admin_approved ? (
                        <span className="inline-flex items-center gap-1.5 rounded-full bg-[var(--color-leaf-500)]/15 px-3 py-1.5 text-xs font-bold text-[var(--color-leaf-300)]">
                          <Check className="h-3.5 w-3.5" /> {fa('تأیید شده', 'Approved')}
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 rounded-full bg-yellow-400/15 px-3 py-1.5 text-xs font-bold text-yellow-700">
                          <X className="h-3.5 w-3.5" /> {fa('در انتظار', 'Pending')}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div>
                      <p className="text-xs text-[var(--color-night-200)]/50 mb-1">{fa('آدرس', 'Address')}</p>
                      <p className="text-sm font-bold text-[var(--color-night-100)]">{marketplace.address || '-'}</p>
                    </div>
                    <div>
                      <p className="text-xs text-[var(--color-night-200)]/50 mb-1">{fa('کد پستی', 'Postal')}</p>
                      <p className="text-sm font-bold text-[var(--color-night-100)]">{marketplace.postal_code || '-'}</p>
                    </div>
                    <div>
                      <p className="text-xs text-[var(--color-night-200)]/50 mb-1">{fa('بنیان‌گذاران', 'Founders')}</p>
                      <p className="text-sm font-bold text-[var(--color-night-100)]">{marketplace.founder_ids?.length || 0}</p>
                    </div>
                    <div>
                      <p className="text-xs text-[var(--color-night-200)]/50 mb-1">{fa('فروشگاه‌ها', 'Shops')}</p>
                      <p className="text-sm font-bold text-[var(--color-night-100)]">{shops.length}</p>
                    </div>
                  </div>
                </div>
              </div>
            </Reveal>

            <Reveal>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-extrabold text-[var(--color-night-100)]">
                  {fa('فروشگاه‌های بازارچه', 'Marketplace Shops')}
                </h2>
                <span className="text-sm text-[var(--color-night-200)]/60">{fa('تعداد', 'Count')}: {shops.length}</span>
              </div>

              {shops.length === 0 ? (
                <div className="text-center py-16 bg-white rounded-3xl border border-[var(--color-sand-200)]">
                  <p className="text-[var(--color-night-200)]/60">{fa('هنوز فروشگاهی ثبت نشده', 'No shops yet')}</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
                  {shops.map((shop) => (
                    <div key={shop.id} className="bg-white rounded-2xl p-4 border border-[var(--color-sand-200)]">
                      <h3 className="font-bold text-[var(--color-night-100)]">{shop.shop_name}</h3>
                      <p className="text-xs text-[var(--color-night-200)]/60 mt-1">
                        {shop.status === 'pending' ? fa('در انتظار', 'Pending') : fa('فعال', 'Active')}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </Reveal>

            {marketplace.marketplace_type === 'rural' && (
              <Reveal>
                <div className="bg-[var(--color-leaf-50)]/30 rounded-3xl p-6 sm:p-8">
                  <h3 className="text-lg font-extrabold text-[var(--color-night-100)] mb-4">🌾 {fa('مزایای بازارچه روستایی', 'Rural Marketplace Benefits')}</h3>
                  <ul className="grid gap-3 sm:grid-cols-2">
                    {[
                      fa('برند سازی محصولات روستایی', 'Brand rural products'),
                      fa('دسترسی مستقیم به مصرف‌کنندگان', 'Direct consumer access'),
                      fa('حفظ هویت فرهنگی روستا', 'Preserve village culture'),
                      fa('تولید پایدار و محیط زیست', 'Sustainable production'),
                      fa('توزیع عادلانه درآمد', 'Fair income distribution'),
                      fa('توانمندسازی زنان روستا', 'Empower rural women'),
                    ].map((item, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm text-[var(--color-night-200)]">
                        <Check className="h-4 w-4 text-[var(--color-leaf-500)]" aria-hidden /> {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </Reveal>
            )}

            {marketplace.marketplace_type === 'tribal' && (
              <Reveal>
                <div className="bg-[var(--color-sand-50)]/50 rounded-3xl p-6 sm:p-8">
                  <h3 className="text-lg font-extrabold text-[var(--color-night-100)] mb-4">🐪 {fa('مزایای بازارچه عشایری', 'Tribal Marketplace Benefits')}</h3>
                  <ul className="grid gap-3 sm:grid-cols-2">
                    {[
                      fa('برند سازی محصولات عشایری', 'Brand tribal products'),
                      fa('حفظ میراث فرهنگی عشایر', 'Preserve tribal heritage'),
                      fa('دسترسی به بازار وسیع', 'Access to wider market'),
                      fa('محصولات منحصربه‌فرد', 'Unique products'),
                      fa('توانمندسازی عشایری‌ها', 'Empower tribal communities'),
                      fa('تولید سنتی و دست‌ساز', 'Traditional craftsmanship'),
                    ].map((item, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm text-[var(--color-night-200)]">
                        <Check className="h-4 w-4 text-[var(--color-leaf-500)]" aria-hidden /> {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </Reveal>
            )}
          </div>
        </main>
      </div>
    </>
  );
}