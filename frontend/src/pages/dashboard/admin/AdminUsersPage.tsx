/** Admin Users - User management page */

import { useState, useEffect } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useBilingual } from '../../../hooks/useBilingual';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { Users, Search, Loader2, Shield, Mail, Phone, UserPlus, Eye, Trash2 } from 'lucide-react';

interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  is_admin: boolean;
  is_active: boolean;
  phone: string | null;
  country: string | null;
  language: string;
  created_at: string;
  last_login: string | null;
}

export default function AdminUsersPage() {
  const { fa } = useBilingual();
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const LIMIT = 20;

  const loadUsers = async () => {
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
      if (roleFilter) params.set('role', roleFilter);
      if (statusFilter) params.set('is_active', statusFilter);

      const res = await fetch(`${apiBase}/api/v1/admin/users?${params.toString()}`, { headers });
      if (!res.ok) throw new Error('Failed to fetch users');
      const data = await res.json();
      setUsers(data.users || []);
      setTotalCount(data.count || 0);
    } catch (err: any) {
      setError(err.message || fa('خطا در بارگذاری', 'Failed to load'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadUsers(); }, [page, searchQuery, roleFilter, statusFilter]);

  const handleToggleActive = async (userId: string, currentStatus: boolean) => {
    setActionLoading(userId);
    try {
      const apiBase = (window as any).API_BASE_URL || 'http://127.0.0.1:8000';
      const token = localStorage.getItem('hydroma_token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      await fetch(`${apiBase}/api/v1/admin/users/${userId}/toggle-active`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ is_active: !currentStatus }),
      });
      loadUsers();
    } catch {
      alert(fa('خطا در تغییر وضعیت', 'Failed to toggle status'));
    } finally {
      setActionLoading(null);
    }
  };

  const handleToggleAdmin = async (userId: string, currentStatus: boolean) => {
    if (!currentUser || userId === currentUser.id) {
      alert(fa('نمی‌توانید وضعیت خود را تغییر دهید', 'Cannot change your own status'));
      return;
    }
    setActionLoading(userId);
    try {
      const apiBase = (window as any).API_BASE_URL || 'http://127.0.0.1:8000';
      const token = localStorage.getItem('hydroma_token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      await fetch(`${apiBase}/api/v1/admin/users/${userId}/toggle-admin`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ is_admin: !currentStatus }),
      });
      loadUsers();
    } catch {
      alert(fa('خطا در تغییر سطح دسترسی', 'Failed to toggle admin'));
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (userId: string) => {
    if (!currentUser || userId === currentUser.id) {
      alert(fa('نمی‌توانید خود را حذف کنید', 'Cannot delete yourself'));
      return;
    }
    if (!confirm(fa('آیا مطمئن هستید؟', 'Are you sure?'))) return;
    setActionLoading(userId);
    try {
      const apiBase = (window as any).API_BASE_URL || 'http://127.0.0.1:8000';
      const token = localStorage.getItem('hydroma_token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      await fetch(`${apiBase}/api/v1/admin/users/${userId}`, {
        method: 'DELETE',
        headers,
      });
      loadUsers();
    } catch {
      alert(fa('خطا در حذف', 'Failed to delete'));
    } finally {
      setActionLoading(null);
    }
  };

  const totalPages = Math.ceil(totalCount / 20);

  if (loading && page === 1) return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-[var(--color-leaf-400)]" /></div>;
  if (error) return <div className="p-6 text-center text-red-400">{error}</div>;

  return (
    <>
      <Seo title={fa('مدیریت کاربران', 'User Management')} path="/dashboard/admin/users" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-7xl">
          <Reveal>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
              <div>
                <h1 className="text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
                  <Users className="h-6 w-6 text-[var(--color-leaf-400)]" />
                  {fa('مدیریت کاربران', 'User Management')}
                </h1>
                <p className="mt-1 text-sm text-[var(--color-night-200)]/60">{fa('مشاهده، جستجو و مدیریت کاربران سیستم', 'View, search and manage system users')}</p>
              </div>
              <a href="/dashboard/admin/users/create" className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--color-leaf-500)] text-white text-sm font-bold hover:bg-[var(--color-leaf-600)] transition">
                <UserPlus className="h-4 w-4" /> {fa('افزودن کاربر', 'Add User')}
              </a>
            </div>
          </Reveal>

          {/* Filters */}
          <Reveal delay={0.1}>
            <div className="glass rounded-2xl p-4 mb-6 flex flex-wrap items-center gap-3">
              <div className="relative flex-1 min-w-[250px]">
                <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-night-200)]/50" />
                <input
                  type="text"
                  placeholder={fa('جستجوی ایمیل، نام...', 'Search email, name...')}
                  value={searchQuery}
                  onChange={e => { setSearchQuery(e.target.value); setPage(1); }}
                  className="w-full pl-10 pr-4 py-2 bg-[var(--color-night-50)] border border-[var(--color-night-200)]/20 rounded-xl text-sm text-[var(--color-night-100)] focus:outline-none focus:ring-2 focus:ring-[var(--color-leaf-400)]"
                />
              </div>
              <div className="flex gap-2">
                <select value={roleFilter} onChange={e => { setRoleFilter(e.target.value); setPage(1); }} className="px-3 py-2 bg-[var(--color-night-50)] border border-[var(--color-night-200)]/20 rounded-xl text-sm text-[var(--color-night-100)] focus:outline-none focus:ring-2 focus:ring-[var(--color-leaf-400)]">
                  <option value="">{fa('همه نقش‌ها', 'All Roles')}</option>
                  <option value="user">{fa('کاربر', 'User')}</option>
                  <option value="admin">{fa('مدیر', 'Admin')}</option>
                  <option value="vendor">{fa('فروشنده', 'Vendor')}</option>
                  <option value="producer">{fa('تولیدکننده', 'Producer')}</option>
                </select>
                <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1); }} className="px-3 py-2 bg-[var(--color-night-50)] border border-[var(--color-night-200)]/20 rounded-xl text-sm text-[var(--color-night-100)] focus:outline-none focus:ring-2 focus:ring-[var(--color-leaf-400)]">
                  <option value="">{fa('همه', 'All')}</option>
                  <option value="true">{fa('فعال', 'Active')}</option>
                  <option value="false">{fa('غیرفعال', 'Inactive')}</option>
                </select>
              </div>
            </div>
          </Reveal>

          {/* Users Table */}
          <Reveal delay={0.2}>
            <div className="glass rounded-2xl overflow-hidden">
              {loading && page === 1 && <div className="p-8 text-center"><Loader2 className="h-8 w-8 animate-spin text-[var(--color-leaf-400)] mx-auto" /></div>}
              <div className="overflow-x-auto">
                <table className="w-full text-sm" dir="ltr">
                  <thead className="bg-[#f6ecd6]"><tr className="text-[var(--color-night-200)]/60 text-[11px] uppercase">
                    <th className="text-right p-3">{fa('نام/ایمیل', 'Name/Email')}</th>
                    <th className="p-3">{fa('نقش', 'Role')}</th>
                    <th className="p-3">{fa('وضعیت', 'Status')}</th>
                    <th className="p-3">{fa('ایمیل/تلفن', 'Contact')}</th>
                    <th className="p-3">{fa('تاریخ ثبت', 'Joined')}</th>
                    <th className="p-3">{fa('آخرین ورود', 'Last Login')}</th>
                    <th className="p-3">{fa('عملیات', 'Actions')}</th>
                  </tr></thead>
                  <tbody>
                    {users.length === 0 ? (
                      <tr><td colSpan={7} className="p-6 text-center text-[var(--color-night-200)]/50">{fa('کاربری یافت نشد', 'No users found')}</td></tr>
                    ) : users.map((u) => (
                      <tr key={u.id} className="border-t border-white/5">
                        <td className="text-right p-3">
                          <div>
                            <p className="font-medium text-[var(--color-night-100)]">{u.full_name || fa('بدون نام', 'No name')}</p>
                            <p className="text-xs text-[var(--color-night-200)]/60 font-mono">{u.email}</p>
                          </div>
                        </td>
                        <td className="p-3">
                          <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${u.is_admin ? 'bg-purple-500/20 text-purple-400' : u.role === 'vendor' ? 'bg-[var(--color-aqua-500)]/20 text-[var(--color-aqua-400)]' : 'bg-[var(--color-night-50)] text-[var(--color-night-200)]/70'}`}>
                            {u.is_admin ? fa('مدیر', 'Admin') : u.role}
                          </span>
                        </td>
                        <td className="p-3">
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" checked={u.is_active} onChange={() => handleToggleActive(u.id, u.is_active)} disabled={actionLoading === u.id} className="w-4 h-4 rounded border-[var(--color-night-200)]/30 text-[var(--color-leaf-500)] focus:ring-[var(--color-leaf-500)]" />
                            <span className="text-xs">{u.is_active ? fa('فعال', 'Active') : fa('غیرفعال', 'Inactive')}</span>
                          </label>
                        </td>
                        <td className="p-3 text-[var(--color-night-200)]/70 text-xs">
                          <div className="flex flex-col gap-1">
                            <div className="flex items-center gap-1"><Mail className="h-3 w-3" /> {u.email}</div>
                            {u.phone && <div className="flex items-center gap-1"><Phone className="h-3 w-3" /> {u.phone}</div>}
                          </div>
                        </td>
                        <td className="p-3 text-xs text-[var(--color-night-200)]/60">{new Date(u.created_at).toLocaleDateString()}</td>
                        <td className="p-3 text-xs text-[var(--color-night-200)]/60">{u.last_login ? new Date(u.last_login).toLocaleDateString() : fa('هرگز', 'Never')}</td>
                        <td className="p-3">
                          <div className="flex items-center gap-2">
                            <a href={`/dashboard/admin/users/${u.id}`} className="text-[var(--color-night-200)]/50 hover:text-[var(--color-leaf-400)]" title={fa('مشاهده', 'View')}>
                              <Eye className="h-4 w-4" />
                            </a>
                            <button onClick={() => handleToggleAdmin(u.id, u.is_admin)} disabled={actionLoading === u.id || !currentUser || u.id === currentUser.id} className="text-[var(--color-night-200)]/50 hover:text-[var(--color-leaf-400)] disabled:opacity-50" title={fa('تغییر سطح دسترسی', 'Toggle Admin')}>
                              <Shield className={`h-4 w-4 ${u.is_admin ? 'text-purple-400' : 'text-[var(--color-night-200)]/50'}`} />
                            </button>
                            <button onClick={() => handleDelete(u.id)} disabled={actionLoading === u.id || !currentUser || u.id === currentUser.id} className="text-[var(--color-night-200)]/50 hover:text-red-400 disabled:opacity-50" title={fa('حذف', 'Delete')}>
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="px-4 py-4 border-t border-white/10 flex items-center justify-between">
                  <p className="text-sm text-[var(--color-night-200)]/60">{fa('صفحه', 'Page')} {page} {fa('از', 'of')} {totalPages} ({totalCount} {fa('کاربر', 'users')})</p>
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