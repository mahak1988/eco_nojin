import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useBilingual } from '../../hooks/useBilingual';
import { fetchMarketplaces } from '../../lib/marketplaceApi';
import type { Marketplace } from '../../lib/marketplaceTypes';
import Seo from '../../components/ui/Seo';
import PageHeader from '../../components/sections/PageHeader';
import Reveal from '../../components/ui/Reveal';
import { Loader2, MapPin, Users, Clock, ArrowRight, Building2, Tag } from 'lucide-react';

export default function MarketplaceDirectory() {
  const { fa } = useBilingual();
  const [marketplaces, setMarketplaces] = useState<Marketplace[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [filterType, setFilterType] = useState<string>('');

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchMarketplaces({ limit: 50 });
        setMarketplaces(data.marketplaces);
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const filtered = filterType
    ? marketplaces.filter((m) => m.marketplace_type === filterType)
    : marketplaces;

  return (
    <>
      <Seo title={fa('بازارچه‌ها', 'Marketplaces')} path="/marketplace/directory" />
      <div className="min-h-screen bg-[var(--color-sand-50)]">
        <PageHeader
          kicker={fa('بازارگاه', 'Marketplace')}
          title={fa('بازارچه‌ها', 'Marketplaces')}
          lead={fa('کشف بازارچه‌های روستایی و عشایری', 'Discover rural and tribal marketplaces')}
        />

        <main className="px-4 py-8 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-6xl">
            <div className="flex flex-wrap gap-2 mb-8">
              <button
                type="button"
                onClick={() => setFilterType('')}
                className={`rounded-full px-4 py-2 text-sm font-bold transition ${
                  !filterType
                    ? 'bg-[var(--color-leaf-500)] text-[var(--color-night-950)]'
                    : 'border border-[var(--color-night-700)]/40 bg-[var(--color-night-800)]/40 text-[var(--color-night-200)]/70 hover:border-[var(--color-leaf-500)]/30'
                }`}
              >
                {fa('همه', 'All')}
              </button>
              <button
                type="button"
                onClick={() => setFilterType('rural')}
                className={`rounded-full px-4 py-2 text-sm font-bold transition ${
                  filterType === 'rural'
                    ? 'bg-[var(--color-leaf-500)] text-[var(--color-night-950)]'
                    : 'border border-[var(--color-night-700)]/40 bg-[var(--color-night-800)]/40 text-[var(--color-night-200)]/70 hover:border-[var(--color-leaf-500)]/30'
                }`}
              >
                🌾 {fa('روستایی', 'Rural')}
              </button>
              <button
                type="button"
                onClick={() => setFilterType('tribal')}
                className={`rounded-full px-4 py-2 text-sm font-bold transition ${
                  filterType === 'tribal'
                    ? 'bg-[var(--color-leaf-500)] text-[var(--color-night-950)]'
                    : 'border border-[var(--color-night-700)]/40 bg-[var(--color-night-800)]/40 text-[var(--color-night-200)]/70 hover:border-[var(--color-leaf-500)]/30'
                }`}
              >
                🐪 {fa('عشایری', 'Tribal')}
              </button>
            </div>

            {loading && (
              <div className="flex flex-col items-center gap-3 py-20">
                <Loader2 className="h-10 w-10 animate-spin rounded-full border-2 border-[var(--color-leaf-500)]/25 border-t-[var(--color-leaf-400)]" />
                <p className="text-sm text-[var(--color-night-200)]/60">{fa('در حال بارگذاری...', 'Loading...')}</p>
              </div>
            )}

            {!loading && error && (
              <div className="flex flex-col items-center gap-3 py-20">
                <p className="text-base font-bold text-[var(--color-red-400)]">{fa('خطا در بارگذاری', 'Error loading')}</p>
                <button
                  type="button"
                  onClick={() => window.location.reload()}
                  className="rounded-full bg-[var(--color-leaf-500)] px-5 py-2 text-xs font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.03]"
                >
                  {fa('تلاش دوباره', 'Retry')}
                </button>
              </div>
            )}

            {!loading && !error && filtered.length === 0 && (
              <div className="flex flex-col items-center gap-3 py-20">
                <p className="text-base text-[var(--color-night-200)]/60">{fa('بازارچه‌ای یافت نشد', 'No marketplaces found')}</p>
              </div>
            )}

            {!loading && !error && filtered.length > 0 && (
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {filtered.map((m, index) => (
                  <Reveal key={m.id} delay={index * 0.05}>
                    <Link
                      to={`/marketplace/marketplaces/${m.id}`}
                      className="group block bg-white rounded-3xl border border-[var(--color-sand-200)] p-6 transition hover:-translate-y-1 hover:shadow-lg"
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="h-12 w-12 rounded-2xl bg-[var(--color-leaf-500)]/15 flex items-center justify-center">
                            <Building2 className="h-6 w-6 text-[var(--color-leaf-400)]" aria-hidden />
                          </div>
                          <div>
                            <h3 className="text-lg font-extrabold text-[var(--color-night-100)]">{m.name}</h3>
                            <p className="text-xs text-[var(--color-night-200)]/60">
                              {m.marketplace_type === 'rural' ? fa('روستایی', 'Rural') : fa('عشایری', 'Tribal')}
                            </p>
                          </div>
                        </div>
                        <ArrowRight className="h-5 w-5 text-[var(--color-night-200)]/30 group-hover:text-[var(--color-leaf-400)] transition" aria-hidden />
                      </div>

                      <p className="text-sm text-[var(--color-night-200)]/60 line-clamp-2 mb-4">
                        {m.description || fa('بدون توضیحات', 'No description')}
                      </p>

                      <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--color-night-200)]/50">
                        <span className="inline-flex items-center gap-1">
                          <MapPin className="h-3 w-3" aria-hidden />
                          {m.location || m.village_id}
                        </span>
                        <span className="inline-flex items-center gap-1">
                          <Users className="h-3 w-3" aria-hidden />
                          {fa('فعال', 'Active')}
                        </span>
                        <span className="inline-flex items-center gap-1">
                          <Clock className="h-3 w-3" aria-hidden />
                          {m.status === 'approved' ? fa('تأیید شده', 'Approved') : fa('در انتظار', 'Pending')}
                        </span>
                        <Tag className="h-3 w-3" aria-hidden />
                        {m.marketplace_type === 'rural' ? fa('محصولات روستایی', 'Rural products') : fa('محصولات عشایری', 'Tribal products')}
                      </div>

                      {m.admin_approved && (
                        <span className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-[var(--color-leaf-500)]/15 px-2.5 py-1 text-[10px] font-bold text-[var(--color-leaf-300)]">
                          <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-leaf-500)]" />
                          {fa('تأیید ادمین', 'Admin Verified')}
                        </span>
                      )}
                    </Link>
                  </Reveal>
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </>
  );
}