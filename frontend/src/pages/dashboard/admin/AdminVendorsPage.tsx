/** Admin Vendors - Vendor approval and management */

import { useState, useEffect } from 'react';
import { useBilingual } from '../../../hooks/useBilingual';
import { adminApproveVendor } from '../../../lib/marketplaceApi';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { Shield, Loader2, Search, Check, X, CheckCircle, XCircle, Clock, MapPin } from 'lucide-react';

interface Vendor {
  id: string;
  shop_name: string;
  description: string;
  status: 'pending' | 'active' | 'suspended' | 'rejected';
  location: string;
  village_id: string;
  created_at: string;
  approved_at: string | null;
  user_id: string;
  owner_email: string;
  contact_phone: string;
}

export default function AdminVendorsPage() {
  const { fa } = useBilingual();
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const LIMIT = 20;

  const loadVendors = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiBase = (window as any).API_BASE_URL || 'http://127.0.0.1:8000';
      const token = localStorage.getItem('hydroma_token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const params = new URLSearchParams();
      params.set('limit', String(LIMIT));
      params.set('offset', String((page - 1) * LIMIT));
      if (searchQuery) params.set('q', searchQuery);
      if (statusFilter) params.set('status', statusFilter);

      const res = await fetch(`${apiBase}/api/v1/admin/vendors?${params.toString()}`, { headers });
      if (!res.ok) throw new Error('Failed to fetch vendors');
      const data = await res.json();
      setVendors(data.vendors || []);
      setTotalCount(data.count || 0);
    } catch (err: any) {
      setError(err.message || fa('خطا در بارگذاری', 'Failed to load'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadVendors(); }, [page, searchQuery, statusFilter]);

  const handleApprove = async (vendorId: string, approve: boolean) => {
    setActionLoading(vendorId);
    try {
      await adminApproveVendor(vendorId, approve);
      loadVendors();
    } catch {
      alert(fa('خطا در تغییر وضعیت', 'Failed to update vendor'));
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { bg: string; text: string; label: string; icon: any }> = {
      pending: { bg: 'bg-[#e8c66b]/20', text: 'text-[#e8c66b]', label: fa('در انتظار', 'Pending'), icon: Clock },
      active: { bg: 'bg-[var(--color-leaf-500)]/20', text: 'text-[var(--color-leaf-400)]', label: fa('فعال', 'Active'), icon: CheckCircle },
      suspended: { bg: 'bg-red-500/20', text: 'text-red-400', label: fa('معلق', 'Suspended'), icon: XCircle },
      rejected: { bg: 'bg-red-500/20', text: 'text-red-400', label: fa('رد شده', 'Rejected'), icon: XCircle },
    };
    const v = variants[status] || variants.pending;
    return (
      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${v.bg} ${v.text}`}>
        <v.icon className="h-3 w-3" aria-hidden /> {v.label}
      </span>
    );
  };

  const totalPages = Math.ceil(totalCount / 20);

  if (loading && page === 1) return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-[var(--color-leaf-400)]" /></div>;
  if (error) return <div className="p-6 text-center text-red-400">{error}</div>;

  const pendingCount = vendors.filter(v => v.status === 'pending').length;
  const activeCount = vendors.filter(v => v.status === 'active').length;

  return (
    <>
      <Seo title={fa('مدیریت فروشندگان', 'Vendor Management')} path="/dashboard/admin/vendors" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-7xl">
          <Reveal>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
              <div>
                <h1 className="text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
                  <Shield className="h-6 w-6 text-[var(--color-leaf-400)]" />
                  {fa('مدیریت فروشندگان', 'Vendor Management')}
                </h1>
                <p className="mt-1 text-sm text-[var(--color-night-200)]/60">{fa('تأیید، معلق و مدیریت فروشندگان بازارگاه', 'Approve, suspend and manage marketplace vendors')}</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="glass rounded-xl p-3 text-center min-w-[100px]">
                  <p className="text-2xl font-extrabold text-[#e8c66b]">{pendingCount}</p>
                  <p className="text-xs text-[var(--color-night-200)]/60">{fa('در انتظار', 'Pending')}</p>
                </div>
                <div className="glass rounded-xl p-3 text-center min-w-[100px]">
                  <p className="text-2xl font-extrabold text-[var(--color-leaf-400)]">{activeCount}</p>
                  <p className="text-xs text-[var(--color-night-200)]/60">{fa('فعال', 'Active')}</p>
                </div>
              </div>
            </div>
          </Reveal>

          {/* Filters */}
          <Reveal delay={0.1}>
            <div className="glass rounded-2xl p-4 mb-6 flex flex-wrap items-center gap-3">
              <div className="relative flex-1 min-w-[250px]">
                <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-night-200)]/50" />
                <input
                  type="text"
                  placeholder={fa('جستجوی نام فروشگاه، ایمیل...', 'Search shop name, email...')}
                  value={searchQuery}
                  onChange={e => { setSearchQuery(e.target.value); setPage(1); }}
                  className="w-full pl-10 pr-4 py-2 bg-[var(--color-night-50)] border border-[var(--color-night-200)]/20 rounded-xl text-sm text-[var(--color-night-100)] focus:outline-none focus:ring-2 focus:ring-[var(--color-leaf-400)]"
                />
              </div>
              <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1); }} className="px-3 py-2 bg-[var(--color-night-50)] border border-[var(--color-night-200)]/20 rounded-xl text-sm text-[var(--color-night-100)] focus:outline-none focus:ring-2 focus:ring-[var(--color-leaf-400)]">
                <option value="">{fa('همه', 'All')}</option>
                <option value="pending">{fa('در انتظار', 'Pending')}</option>
                <option value="active">{fa('فعال', 'Active')}</option>
                <option value="suspended">{fa('معلق', 'Suspended')}</option>
                <option value="rejected">{fa('رد شده', 'Rejected')}</option>
              </select>
            </div>
          </Reveal>

          {/* Vendors Table */}
          <Reveal delay={0.2}>
            <div className="glass rounded-2xl overflow-hidden">
              {loading && page === 1 && <div className="p-8 text-center"><Loader2 className="h-8 w-8 animate-spin text-[var(--color-leaf-400)] mx-auto" /></div>}
              <div className="overflow-x-auto">
                <table className="w-full text-sm" dir="ltr">
                  <thead className="bg-[#f6ecd6]"><tr className="text-[var(--color-night-200)]/60 text-[11px] uppercase">
                    <th className="text-right p-3">{fa('نام فروشگاه', 'Shop Name')}</th>
                    <th className="p-3">{fa('صاحب', 'Owner')}</th>
                    <th className="p-3">{fa('موقعیت', 'Location')}</th>
                    <th className="p-3">{fa('وضعیت', 'Status')}</th>
                    <th className="p-3">{fa('تاریخ ثبت', 'Registered')}</th>
                    <th className="p-3">{fa('عملیات', 'Actions')}</th>
                  </tr></thead>
                  <tbody>
                    {vendors.length === 0 ? (
                      <tr><td colSpan={6} className="p-6 text-center text-[var(--color-night-200)]/50">{fa('فروشنده‌ای یافت نشد', 'No vendors found')}</td></tr>
                    ) : vendors.map((v) => (
                      <tr key={v.id} className="border-t border-white/5">
                        <td className="text-right p-3">
                          <div>
                            <p className="font-medium text-[var(--color-night-100)]">{v.shop_name}</p>
                            <p className="text-xs text-[var(--color-night-200)]/60">{v.description?.slice(0, 50)}...</p>
                          </div>
                        </td>
                        <td className="p-3 text-[var(--color-night-200)]/70 text-xs">
                          <p>{v.owner_email}</p>
                        </td>
                        <td className="p-3 text-[var(--color-night-200)]/70 text-xs flex items-center gap-1">
                          <MapPin className="h-3 w-3" /> {v.location || v.village_id}
                        </td>
                        <td className="p-3">{getStatusBadge(v.status)}</td>
                        <td className="p-3 text-xs text-[var(--color-night-200)]/60">{new Date(v.created_at).toLocaleDateString()}</td>
                        <td className="p-3">
                          <div className="flex items-center gap-2">
                            {v.status === 'pending' && (
                              <>
                                <button onClick={() => handleApprove(v.id, true)} disabled={actionLoading === v.id} className="p-2 text-[var(--color-leaf-400)] hover:bg-[var(--color-leaf-500)]/10 rounded-lg transition" title={fa('تأیید', 'Approve')}>
                                  {actionLoading === v.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                                </button>
                                <button onClick={() => handleApprove(v.id, false)} disabled={actionLoading === v.id} className="p-2 text-red-400 hover:bg-red-500/10 rounded-lg transition" title={fa('رد/معلق', 'Reject')}>
                                  {actionLoading === v.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <X className="h-4 w-4" />}
                                </button>
                              </>
                            )}
                            {v.status !== 'pending' && (
                              <span className="text-[var(--color-night-200)]/50 text-xs">{fa('پردازش شده', 'Processed')}</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {totalPages > 1 && (
                <div className="px-4 py-4 border-t border-white/10 flex items-center justify-between">
                  <p className="text-sm text-[var(--color-night-200)]/60">{fa('صفحه', 'Page')} {page} {fa('از', 'of')} {totalPages} ({totalCount} {fa('فروشنده', 'vendors')})</p>
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