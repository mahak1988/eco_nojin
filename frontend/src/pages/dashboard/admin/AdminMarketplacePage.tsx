/** Admin Marketplace - Marketplace and village management */

import { useState, useEffect } from 'react';
import { useBilingual } from '../../../hooks/useBilingual';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { Loader2, Search, MapPin, CheckCircle, XCircle, Clock, AlertCircle, Plus, Edit, Eye, Globe } from 'lucide-react';

interface Marketplace {
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'pending_approval' | 'approved' | 'rejected' | 'suspended';
  village_id: string;
  village_name: string;
  e_commerce_rules_accepted: boolean;
  buy_sell_rules_accepted: boolean;
  created_at: string;
  approved_at: string | null;
  owner_id: string;
  owner_email: string;
  vendor_count: number;
  product_count: number;
  monthly_gmv: number;
}

interface Village {
  id: string;
  name: string;
  region: string;
  status: 'active' | 'inactive';
  marketplace_count: number;
  vendor_count: number;
}

export default function AdminMarketplacePage() {
  const { fa } = useBilingual();
  const [marketplaces, setMarketplaces] = useState<Marketplace[]>([]);
  const [villages, setVillages] = useState<Village[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab] = useState<'marketplaces' | 'villages'>('marketplaces');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const LIMIT = 20;

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiBase = (window as any).API_BASE_URL || 'http://127.0.0.1:8000';
      const token = localStorage.getItem('hydroma_token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      if (activeTab === 'marketplaces') {
        const params = new URLSearchParams();
        params.set('limit', String(LIMIT));
        params.set('offset', String((page - 1) * LIMIT));
        if (searchQuery) params.set('q', searchQuery);
        if (statusFilter) params.set('status', statusFilter);

        const res = await fetch(`${apiBase}/api/v1/admin/marketplaces?${params.toString()}`, { headers });
        if (!res.ok) throw new Error('Failed to fetch marketplaces');
        const data = await res.json();
        setMarketplaces(data.marketplaces || []);
        setTotalCount(data.count || 0);
      } else {
        const params = new URLSearchParams();
        params.set('limit', String(LIMIT));
        params.set('offset', String((page - 1) * LIMIT));
        if (searchQuery) params.set('q', searchQuery);

        const res = await fetch(`${apiBase}/api/v1/admin/villages?${params.toString()}`, { headers });
        if (!res.ok) throw new Error('Failed to fetch villages');
        const data = await res.json();
        setVillages(data.villages || []);
        setTotalCount(data.count || 0);
      }
    } catch (err: any) {
      setError(err.message || fa('خطا در بارگذاری', 'Failed to load'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [activeTab, page, searchQuery, statusFilter]);

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { bg: string; text: string; label: string; icon: any }> = {
      draft: { bg: 'bg-[var(--color-night-50)]', text: 'text-[var(--color-night-200)]/70', label: fa('پیش‌نویس', 'Draft'), icon: MapPin },
      pending_approval: { bg: 'bg-[#e8c66b]/20', text: 'text-[#e8c66b]', label: fa('در انتظار تأیید', 'Pending Approval'), icon: Clock },
      approved: { bg: 'bg-[var(--color-leaf-500)]/20', text: 'text-[var(--color-leaf-400)]', label: fa('تأیید شده', 'Approved'), icon: CheckCircle },
      rejected: { bg: 'bg-red-500/20', text: 'text-red-400', label: fa('رد شده', 'Rejected'), icon: XCircle },
      suspended: { bg: 'bg-red-500/20', text: 'text-red-400', label: fa('معلق', 'Suspended'), icon: AlertCircle },
    };
    const v = variants[status] || variants.draft;
    return (
      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${v.bg} ${v.text}`}>
        <v.icon className="h-3 w-3" aria-hidden /> {v.label}
      </span>
    );
  };

  const handleStatusChange = async (id: string, newStatus: string) => {
    setActionLoading(id);
    try {
      const apiBase = (window as any).API_BASE_URL || 'http://127.0.0.1:8000';
      const token = localStorage.getItem('hydroma_token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      await fetch(`${apiBase}/api/v1/admin/marketplaces/${id}/status`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ status: newStatus }),
      });
      loadData();
    } catch {
      alert(fa('خطا در تغییر وضعیت', 'Failed to update status'));
    } finally {
      setActionLoading(null);
    }
  };

  const totalPages = Math.ceil(totalCount / LIMIT);

  if (loading && page === 1) return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-[var(--color-leaf-400)]" /></div>;
  if (error) return <div className="p-6 text-center text-red-400">{error}</div>;

  const stats = activeTab === 'marketplaces' ? {
    total: marketplaces.length,
    approved: marketplaces.filter(m => m.status === 'approved').length,
    pending: marketplaces.filter(m => m.status === 'pending_approval').length,
    suspended: marketplaces.filter(m => m.status === 'suspended').length,
  } : {
    total: villages.length,
    active: villages.filter(v => v.status === 'active').length,
    inactive: villages.filter(v => v.status === 'inactive').length,
  };

  return (
    <>
      <Seo title={fa('مدیریت بازارگاه', 'Marketplace Management')} path="/dashboard/admin/marketplace" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-7xl">
          <Reveal>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
              <div>
                <h1 className="text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
                  <Globe className="h-6 w-6 text-[var(--color-leaf-400)]" />
                  {fa('مدیریت بازارگاه', 'Marketplace Management')}
                </h1>
                <p className="mt-1 text-sm text-[var(--color-night-200)]/60">{activeTab === 'marketplaces' ? fa('مدیریت بازارگاه‌ها و وضعیات', 'Manage marketplaces and their statuses') : fa('مدیریت روستاها و مناطق', 'Manage villages and regions')}</p>
              </div>
              <div className="flex items-center gap-2">
                {activeTab === 'marketplaces' && (
                  <a href="/dashboard/admin/marketplace/create" className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--color-leaf-500)] text-white text-sm font-bold hover:bg-[var(--color-leaf-600)] transition">
                    <Plus className="h-4 w-4" /> {fa('ایجاد بازارگاه', 'Create Marketplace')}
                  </a>
                )}
                {(() => {
                  const label = activeTab === 'marketplaces' ? fa('مشاهده روستاها', 'View Villages') : fa('مشاهده بازارگاه‌ها', 'View Marketplaces');
                  return (
                    <a href={`/dashboard/admin/marketplace?tab=${activeTab === 'marketplaces' ? 'villages' : 'marketplaces'}`} className="px-4 py-2 rounded-xl bg-[var(--color-night-50)] text-[var(--color-night-200)]/70 text-sm font-medium hover:bg-[var(--color-leaf-500)]/10 hover:text-[var(--color-leaf-400)] transition">
                      {label}
                    </a>
                  );
                })()}
              </div>
            </div>
          </Reveal>

          {/* Stats Cards */}
          <Reveal delay={0.05}>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
              {activeTab === 'marketplaces' ? (
                <>
                  <div className="glass rounded-2xl p-4"><p className="text-xs text-[var(--color-night-200)]/60">{fa('کل', 'Total')}</p><p className="text-2xl font-extrabold text-[var(--color-night-100)]">{stats.total}</p></div>
                  <div className="glass rounded-2xl p-4"><p className="text-xs text-[var(--color-night-200)]/60">{fa('تأیید شده', 'Approved')}</p><p className="text-2xl font-extrabold text-[var(--color-leaf-400)]">{stats.approved}</p></div>
                  <div className="glass rounded-2xl p-4"><p className="text-xs text-[var(--color-night-200)]/60">{fa('در انتظار', 'Pending')}</p><p className="text-2xl font-extrabold text-[#e8c66b]">{stats.pending}</p></div>
                  <div className="glass rounded-2xl p-4"><p className="text-xs text-[var(--color-night-200)]/60">{fa('معلق', 'Suspended')}</p><p className="text-2xl font-extrabold text-red-400">{stats.suspended}</p></div>
                </>
              ) : (
                <>
                  <div className="glass rounded-2xl p-4"><p className="text-xs text-[var(--color-night-200)]/60">{fa('کل', 'Total')}</p><p className="text-2xl font-extrabold text-[var(--color-night-100)]">{stats.total}</p></div>
                  <div className="glass rounded-2xl p-4"><p className="text-xs text-[var(--color-night-200)]/60">{fa('فعال', 'Active')}</p><p className="text-2xl font-extrabold text-[var(--color-leaf-400)]">{stats.active}</p></div>
                  <div className="glass rounded-2xl p-4"><p className="text-xs text-[var(--color-night-200)]/60">{fa('غیرفعال', 'Inactive')}</p><p className="text-2xl font-extrabold text-[var(--color-night-200)]/50">{stats.inactive}</p></div>
                  <div className="glass rounded-2xl p-4"><p className="text-xs text-[var(--color-night-200)]/60">{fa('فروشندگان', 'Vendors')}</p><p className="text-2xl font-extrabold text-[var(--color-aqua-400)]">{villages.reduce((a, v) => a + v.vendor_count, 0)}</p></div>
                </>
              )}
            </div>
          </Reveal>

          {/* Filters */}
          <Reveal delay={0.1}>
            <div className="glass rounded-2xl p-4 mb-6 flex flex-wrap items-center gap-3">
              <div className="relative flex-1 min-w-[250px]">
                <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-night-200)]/50" />
                <input
                  type="text"
                  placeholder={activeTab === 'marketplaces' ? fa('جستجوی نام بازارگاه...', 'Search marketplace name...') : fa('جستجوی نام روستا...', 'Search village name...')}
                  value={searchQuery}
                  onChange={e => { setSearchQuery(e.target.value); setPage(1); }}
                  className="w-full pl-10 pr-4 py-2 bg-[var(--color-night-50)] border border-[var(--color-night-200)]/20 rounded-xl text-sm text-[var(--color-night-100)] focus:outline-none focus:ring-2 focus:ring-[var(--color-leaf-400)]"
                />
              </div>
              {activeTab === 'marketplaces' && (
                <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1); }} className="px-3 py-2 bg-[var(--color-night-50)] border border-[var(--color-night-200)]/20 rounded-xl text-sm text-[var(--color-night-100)] focus:outline-none focus:ring-2 focus:ring-[var(--color-leaf-400)]">
                  <option value="">{fa('همه', 'All')}</option>
                  <option value="draft">{fa('پیش‌نویس', 'Draft')}</option>
                  <option value="pending_approval">{fa('در انتظار تأیید', 'Pending Approval')}</option>
                  <option value="approved">{fa('تأیید شده', 'Approved')}</option>
                  <option value="rejected">{fa('رد شده', 'Rejected')}</option>
                  <option value="suspended">{fa('معلق', 'Suspended')}</option>
                </select>
              )}
            </div>
          </Reveal>

          {/* Table */}
          <Reveal delay={0.2}>
            <div className="glass rounded-2xl overflow-hidden">
              {loading && page === 1 && <div className="p-8 text-center"><Loader2 className="h-8 w-8 animate-spin text-[var(--color-leaf-400)] mx-auto" /></div>}
              <div className="overflow-x-auto">
                <table className="w-full text-sm" dir="ltr">
                  <thead className="bg-[#f6ecd6]">
                    <tr className="text-[var(--color-night-200)]/60 text-[11px] uppercase">
                      {activeTab === 'marketplaces' ? (
                        <>
                          <th className="text-right p-3">{fa('نام', 'Name')}</th>
                          <th className="p-3">{fa('روستا', 'Village')}</th>
                          <th className="p-3">{fa('صاحب', 'Owner')}</th>
                          <th className="p-3">{fa('وضعیت', 'Status')}</th>
                          <th className="p-3">{fa('فروشندگان', 'Vendors')}</th>
                          <th className="p-3">{fa('محصولات', 'Products')}</th>
                          <th className="p-3">{fa('GMV ماهانه', 'Monthly GMV')}</th>
                          <th className="p-3">{fa('عملیات', 'Actions')}</th>
                        </>
                      ) : (
                        <>
                          <th className="text-right p-3">{fa('نام روستا', 'Village Name')}</th>
                          <th className="p-3">{fa('منطقه', 'Region')}</th>
                          <th className="p-3">{fa('وضعیت', 'Status')}</th>
                          <th className="p-3">{fa('بازارگاه‌ها', 'Marketplaces')}</th>
                          <th className="p-3">{fa('فروشندگان', 'Vendors')}</th>
                          <th className="p-3">{fa('عملیات', 'Actions')}</th>
                        </>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {activeTab === 'marketplaces' ? (
                      marketplaces.length === 0 ? (
                        <tr><td colSpan={8} className="p-6 text-center text-[var(--color-night-200)]/50">{fa('بازارگاهی یافت نشد', 'No marketplaces found')}</td></tr>
                      ) : marketplaces.map((m) => (
                        <tr key={m.id} className="border-t border-white/5">
                          <td className="text-right p-3">
                            <div>
                              <p className="font-medium text-[var(--color-night-100)]">{m.name}</p>
                              <p className="text-xs text-[var(--color-night-200)]/60">{m.description?.slice(0, 40)}...</p>
                            </div>
                          </td>
                          <td className="p-3 text-[var(--color-night-200)]/70 flex items-center gap-1"><MapPin className="h-3 w-3" /> {m.village_name}</td>
                          <td className="p-3 text-[var(--color-night-200)]/70 text-xs">{m.owner_email}</td>
                          <td className="p-3">{getStatusBadge(m.status)}</td>
                          <td className="p-3 text-xs text-[var(--color-night-200)]/60">{m.vendor_count}</td>
                          <td className="p-3 text-xs text-[var(--color-night-200)]/60">{m.product_count}</td>
                          <td className="p-3 text-xs text-[var(--color-night-200)]/60 font-mono">{m.monthly_gmv.toLocaleString()} {fa('تومن', 'Tmn')}</td>
                          <td className="p-3">
                            <div className="flex items-center gap-2">
                              <a href={`/dashboard/admin/marketplace/${m.id}`} className="text-[var(--color-night-200)]/50 hover:text-[var(--color-leaf-400)]" title={fa('مشاهده', 'View')}>
                                <Eye className="h-4 w-4" />
                              </a>
                              {m.status === 'pending_approval' && (
                                <>
                                  <button onClick={() => handleStatusChange(m.id, 'approved')} disabled={actionLoading === m.id} className="p-2 text-[var(--color-leaf-400)] hover:bg-[var(--color-leaf-500)]/10 rounded-lg" title={fa('تأیید', 'Approve')}>
                                    {actionLoading === m.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
                                  </button>
                                  <button onClick={() => handleStatusChange(m.id, 'rejected')} disabled={actionLoading === m.id} className="p-2 text-red-400 hover:bg-red-500/10 rounded-lg" title={fa('رد', 'Reject')}>
                                    {actionLoading === m.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <XCircle className="h-4 w-4" />}
                                  </button>
                                </>
                              )}
                              {m.status === 'approved' && (
                                <button onClick={() => handleStatusChange(m.id, 'suspended')} disabled={actionLoading === m.id} className="p-2 text-red-400 hover:bg-red-500/10 rounded-lg" title={fa('معلق کردن', 'Suspend')}>
                                  {actionLoading === m.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <AlertCircle className="h-4 w-4" />}
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))
                    ) : (
                      villages.length === 0 ? (
                        <tr><td colSpan={6} className="p-6 text-center text-[var(--color-night-200)]/50">{fa('روستایی یافت نشد', 'No villages found')}</td></tr>
                      ) : villages.map((v) => (
                        <tr key={v.id} className="border-t border-white/5">
                          <td className="text-right p-3">
                            <p className="font-medium text-[var(--color-night-100)]">{v.name}</p>
                          </td>
                          <td className="p-3 text-[var(--color-night-200)]/70">{v.region}</td>
                          <td className="p-3">
                            <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${v.status === 'active' ? 'bg-[var(--color-leaf-500)]/20 text-[var(--color-leaf-400)]' : 'bg-[var(--color-night-50)] text-[var(--color-night-200)]/70'}`}>
                              {v.status === 'active' ? <CheckCircle className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                              {v.status === 'active' ? fa('فعال', 'Active') : fa('غیرفعال', 'Inactive')}
                            </span>
                          </td>
                          <td className="p-3 text-xs text-[var(--color-night-200)]/60">{v.marketplace_count}</td>
                          <td className="p-3 text-xs text-[var(--color-night-200)]/60">{v.vendor_count}</td>
                          <td className="p-3">
                            <div className="flex items-center gap-2">
                              <a href={`/dashboard/admin/marketplace/village/${v.id}`} className="text-[var(--color-night-200)]/50 hover:text-[var(--color-leaf-400)]" title={fa('مشاهده', 'View')}>
                                <Eye className="h-4 w-4" />
                              </a>
                              <a href={`/dashboard/admin/marketplace/village/${v.id}/edit`} className="text-[var(--color-night-200)]/50 hover:text-[var(--color-leaf-400)]" title={fa('ویرایش', 'Edit')}>
                                <Edit className="h-4 w-4" />
                              </a>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {totalPages > 1 && (
                <div className="px-4 py-4 border-t border-white/10 flex items-center justify-between">
                  <p className="text-sm text-[var(--color-night-200)]/60">{fa('صفحه', 'Page')} {page} {fa('از', 'of')} {totalPages} ({totalCount} {fa('مورد', 'items')})</p>
                  <div className="flex items-center gap-2">
                    <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="p-2 rounded-lg bg-[var(--color-night-50)] hover:bg-[var(--color-leaf-500)]/10 disabled:opacity-50"><ChevronRight className="h-4 w-4" /></button>
                    <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="p-2 rounded-lg bg-[var(--color-night-50)] hover:bg-[var(--color-leaf-500)]/10 disabled:opacity-50"><ChevronLeft className="h-4 w-4" /></button>
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

function ChevronRight(props: React.SVGProps<SVGSVGElement>) { return <svg {...props} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>; }
function ChevronLeft(props: React.SVGProps<SVGSVGElement>) { return <svg {...props} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>; }