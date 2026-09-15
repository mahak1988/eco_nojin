import { useState, useEffect } from 'react';
import { useBilingual } from '../../hooks/useBilingual';
import { fetchMarketplaces, fetchMarketplaceShops } from '../../lib/marketplaceApi';
import type { Marketplace } from '../../lib/marketplaceTypes';
import Seo from '../../components/ui/Seo';
import PageHeader from '../../components/sections/PageHeader';
import Reveal from '../../components/ui/Reveal';
import { Loader2, Building2, Store, Check, Plus, TrendingUp } from 'lucide-react';

export default function MarketplaceDashboard() {
  const { fa } = useBilingual();
  const [marketplaces, setMarketplaces] = useState<Marketplace[]>([]);
  const [shops, setShops] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchMarketplaces({ limit: 50 });
        setMarketplaces(data.marketplaces);
        for (const m of data.marketplaces) {
          const shopsData = await fetchMarketplaceShops(m.id);
          setShops(prev => ({ ...prev, [m.id]: shopsData.shops.length }));
        }
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const totalShops = Object.values(shops).reduce((a, b) => a + b, 0);
  const approvedCount = marketplaces.filter((m) => m.admin_approved).length;
  const pendingCount = marketplaces.filter((m) => m.status === 'pending').length;

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="h-10 w-10 animate-spin text-[var(--color-leaf-400)]" />
      </div>
    );
  }

  return (
    <>
      <Seo title={fa('داشبورد بازارچه', 'Marketplace Dashboard')} path="/marketplace/dashboard" />
      <div className="min-h-screen bg-[var(--color-sand-50)]">
        <PageHeader
          kicker={fa('مدیریت', 'Management')}
          title={fa('داشبورد بازارچه', 'Marketplace Dashboard')}
          lead={fa('مدیریت بازارچه‌ها و فروشگاه‌ها', 'Manage marketplaces and shops')}
        />

        <main className="px-4 py-8 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-6xl">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <Reveal>
                <div className="glass rounded-2xl p-4 text-center">
                  <Building2 className="h-6 w-6 mx-auto mb-2 text-[var(--color-leaf-400)]" aria-hidden />
                  <p className="text-2xl font-extrabold text-[var(--color-night-100)]">{marketplaces.length}</p>
                  <p className="text-xs text-[var(--color-night-200)]/60">{fa('بازارچه', 'Marketplaces')}</p>
                </div>
              </Reveal>
              <Reveal delay={0.05}>
                <div className="glass rounded-2xl p-4 text-center">
                  <Store className="h-6 w-6 mx-auto mb-2 text-[var(--color-leaf-400)]" aria-hidden />
                  <p className="text-2xl font-extrabold text-[var(--color-night-100)]">{totalShops}</p>
                  <p className="text-xs text-[var(--color-night-200)]/60">{fa('فروشگاه', 'Shops')}</p>
                </div>
              </Reveal>
              <Reveal delay={0.1}>
                <div className="glass rounded-2xl p-4 text-center">
                  <Check className="h-6 w-6 mx-auto mb-2 text-[var(--color-leaf-400)]" aria-hidden />
                  <p className="text-2xl font-extrabold text-[var(--color-night-100)]">{approvedCount}</p>
                  <p className="text-xs text-[var(--color-night-200)]/60">{fa('تأیید شده', 'Approved')}</p>
                </div>
              </Reveal>
              <Reveal delay={0.15}>
                <div className="glass rounded-2xl p-4 text-center">
                  <TrendingUp className="h-6 w-6 mx-auto mb-2 text-[var(--color-sand-400)]" aria-hidden />
                  <p className="text-2xl font-extrabold text-[var(--color-night-100)]">{pendingCount}</p>
                  <p className="text-xs text-[var(--color-night-200)]/60">{fa('در انتظار', 'Pending')}</p>
                </div>
              </Reveal>
            </div>

            <Reveal>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-extrabold text-[var(--color-night-100)]">{fa('لیست بازارچه‌ها', 'Marketplaces')}</h2>
                <button
                  type="button"
                  onClick={() => { /* navigate to create */ }}
                  className="inline-flex items-center gap-2 rounded-full bg-[var(--color-leaf-500)] px-4 py-2 text-xs font-extrabold text-[var(--color-night-950)] hover:bg-[var(--color-leaf-400)] transition"
                >
                  <Plus className="h-4 w-4" /> {fa('ایجاد بازارچه', 'Create')}
                </button>
              </div>

              {marketplaces.length === 0 ? (
                <div className="text-center py-16 bg-white rounded-3xl border border-[var(--color-sand-200)]">
                  <p className="text-[var(--color-night-200)]/60">{fa('هنوز بازارچه‌ای ثبت نشده', 'No marketplaces yet')}</p>
                </div>
              ) : (
                <div className="glass rounded-3xl overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-white/5">
                      <tr className="text-[var(--color-night-200)]/60 text-[11px] uppercase">
                        <th className="text-right p-3">{fa('نام', 'Name')}</th>
                        <th className="p-3">{fa('نوع', 'Type')}</th>
                        <th className="p-3">{fa('فروشگاه‌ها', 'Shops')}</th>
                        <th className="p-3">{fa('وضعیت', 'Status')}</th>
                        <th className="p-3">{fa('تاریخ', 'Date')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {marketplaces.map((m) => (
                        <tr key={m.id} className="border-t border-white/5 hover:bg-white/5">
                          <td className="text-right p-3 text-[var(--color-night-100)] font-bold">
                            <span className="cursor-pointer hover:text-[var(--color-leaf-400)]">{m.name}</span>
                          </td>
                          <td className="p-3 text-[var(--color-night-200)]/60">
                            {m.marketplace_type === 'rural' ? '🌾 ' + fa('روستایی', 'Rural') : '🐪 ' + fa('عشایری', 'Tribal')}
                          </td>
                          <td className="p-3 text-[var(--color-night-200)]/60">{shops[m.id] || 0}</td>
                          <td className="p-3">
                            {m.admin_approved ? (
                              <span className="rounded-full bg-[var(--color-leaf-500)]/15 px-2 py-0.5 text-[10px] font-bold text-[var(--color-leaf-300)]">{fa('تأیید', 'OK')}</span>
                            ) : m.status === 'pending' ? (
                              <span className="rounded-full bg-yellow-400/15 px-2 py-0.5 text-[10px] font-bold text-yellow-700">{fa('در انتظار', 'Pending')}</span>
                            ) : (
                              <span className="rounded-full bg-red-400/15 px-2 py-0.5 text-[10px] font-bold text-red-400">{fa('رد شده', 'Rejected')}</span>
                            )}
                          </td>
                          <td className="p-3 text-[var(--color-night-200)]/50">
                            {new Date(m.created_at).toLocaleDateString('fa-IR')}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Reveal>
          </div>
        </main>
      </div>
    </>
  );
}