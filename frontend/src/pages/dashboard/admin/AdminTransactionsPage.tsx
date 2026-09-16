/** Admin Transactions - Financial transaction monitoring */

import { useState, useEffect } from 'react';
import { useBilingual } from '../../../hooks/useBilingual';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { Loader2, Search, DollarSign, CreditCard, Wallet, ArrowUpRight, ArrowDownLeft, MinusCircle, CheckCircle, XCircle, Clock, Download, Eye } from 'lucide-react';

interface Transaction {
  id: string;
  type: 'payment' | 'refund' | 'payout' | 'fee' | 'earn' | 'spend' | 'transfer';
  status: 'pending' | 'completed' | 'failed' | 'cancelled' | 'refunded';
  amount: number;
  currency: string;
  user_id: string;
  user_email: string;
  user_name: string;
  related_order_id: string | null;
  related_settlement_id: string | null;
  description: string;
  created_at: string;
  completed_at: string | null;
  metadata: Record<string, any>;
}

export default function AdminTransactionsPage() {
  const { fa } = useBilingual();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const LIMIT = 25;

  const loadTransactions = async () => {
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
      if (typeFilter) params.set('type', typeFilter);
      if (statusFilter) params.set('status', statusFilter);

      const res = await fetch(`${apiBase}/api/v1/admin/transactions?${params.toString()}`, { headers });
      if (!res.ok) throw new Error('Failed to fetch transactions');
      const data = await res.json();
      setTransactions(data.transactions || []);
      setTotalCount(data.count || 0);
    } catch (err: any) {
      setError(err.message || fa('خطا در بارگذاری', 'Failed to load'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadTransactions(); }, [page, searchQuery, typeFilter, statusFilter]);

  const getTypeInfo = (type: string) => {
    const variants: Record<string, { label: string; icon: any; color: string }> = {
      payment: { label: fa('پرداخت', 'Payment'), icon: CreditCard, color: 'text-[var(--color-leaf-400)]' },
      refund: { label: fa('بازپرداخت', 'Refund'), icon: ArrowDownLeft, color: 'text-blue-400' },
      payout: { label: fa('تسویه', 'Payout'), icon: Wallet, color: 'text-purple-400' },
      fee: { label: fa('کارمزد', 'Fee'), icon: MinusCircle, color: 'text-orange-400' },
      earn: { label: fa('برداشت', 'Earn'), icon: ArrowUpRight, color: 'text-[var(--color-aqua-400)]' },
      spend: { label: fa('خرید', 'Spend'), icon: ArrowDownLeft, color: 'text-red-400' },
      transfer: { label: fa('انتقال', 'Transfer'), icon: Wallet, color: 'text-yellow-400' },
    };
    return variants[type] || { label: type, icon: DollarSign, color: 'text-[var(--color-night-200)]/60' };
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { bg: string; text: string; label: string; icon: any }> = {
      pending: { bg: 'bg-[#e8c66b]/20', text: 'text-[#e8c66b]', label: fa('در انتظار', 'Pending'), icon: Clock },
      completed: { bg: 'bg-[var(--color-leaf-500)]/20', text: 'text-[var(--color-leaf-400)]', label: fa('تکمیل', 'Completed'), icon: CheckCircle },
      failed: { bg: 'bg-red-500/20', text: 'text-red-400', label: fa('ناموفق', 'Failed'), icon: XCircle },
      cancelled: { bg: 'bg-[var(--color-night-50)]', text: 'text-[var(--color-night-200)]/60', label: fa('لغو', 'Cancelled'), icon: XCircle },
      refunded: { bg: 'bg-blue-500/20', text: 'text-blue-400', label: fa('بازپرداخت شده', 'Refunded'), icon: ArrowDownLeft },
    };
    const v = variants[status] || variants.pending;
    return (
      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${v.bg} ${v.text}`}>
        <v.icon className="h-3 w-3" aria-hidden /> {v.label}
      </span>
    );
  };

  const formatAmount = (amount: number, currency: string) => {
    return `${amount.toLocaleString()} ${currency.toUpperCase()}`;
  };

  const totalPages = Math.ceil(totalCount / LIMIT);

  const totalVolume = transactions.reduce((sum, t) => sum + t.amount, 0);
  const pendingCount = transactions.filter(t => t.status === 'pending').length;
  const completedCount = transactions.filter(t => t.status === 'completed').length;
  const failedCount = transactions.filter(t => t.status === 'failed').length;

  if (loading && page === 1) return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-[var(--color-leaf-400)]" /></div>;
  if (error) return <div className="p-6 text-center text-red-400">{error}</div>;

  return (
    <>
      <Seo title={fa('مدیریت تراکنش‌ها', 'Transaction Management')} path="/dashboard/admin/transactions" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-7xl">
          <Reveal>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
              <div>
                <h1 className="text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
                  <DollarSign className="h-6 w-6 text-[var(--color-leaf-400)]" />
                  {fa('مدیریت تراکنش‌ها', 'Transaction Management')}
                </h1>
                <p className="mt-1 text-sm text-[var(--color-night-200)]/60">{fa('نظارت بر تمام تراکنش‌های مالی سیستم', 'Monitor all financial transactions')}</p>
              </div>
              <a href="/dashboard/admin/transactions/export" className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--color-night-50)] text-[var(--color-night-200)]/70 text-sm font-medium hover:bg-[var(--color-leaf-500)]/10 hover:text-[var(--color-leaf-400)] transition">
                <Download className="h-4 w-4" /> {fa('صادرات', 'Export')}
              </a>
            </div>
          </Reveal>

          {/* Summary Cards */}
          <Reveal delay={0.05}>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mb-6">
              <div className="glass rounded-2xl p-4"><p className="text-xs text-[var(--color-night-200)]/60">{fa('حجم کل', 'Total Volume')}</p><p className="text-xl font-extrabold text-[var(--color-night-100)]">{totalVolume.toLocaleString()} IRR</p></div>
              <div className="glass rounded-2xl p-4"><p className="text-xs text-[var(--color-night-200)]/60">{fa('تکمیل شده', 'Completed')}</p><p className="text-xl font-extrabold text-[var(--color-leaf-400)]">{completedCount}</p></div>
              <div className="glass rounded-2xl p-4"><p className="text-xs text-[var(--color-night-200)]/60">{fa('در انتظار', 'Pending')}</p><p className="text-xl font-extrabold text-[#e8c66b]">{pendingCount}</p></div>
              <div className="glass rounded-2xl p-4"><p className="text-xs text-[var(--color-night-200)]/60">{fa('ناموفق', 'Failed')}</p><p className="text-xl font-extrabold text-red-400">{failedCount}</p></div>
              <div className="glass rounded-2xl p-4"><p className="text-xs text-[var(--color-night-200)]/60">{fa('تعداد', 'Count')}</p><p className="text-xl font-extrabold text-[var(--color-night-100)]">{totalCount}</p></div>
            </div>
          </Reveal>

          {/* Filters */}
          <Reveal delay={0.1}>
            <div className="glass rounded-2xl p-4 mb-6 flex flex-wrap items-center gap-3">
              <div className="relative flex-1 min-w-[250px]">
                <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-night-200)]/50" />
                <input
                  type="text"
                  placeholder={fa('جستجوی کاربر، توضیحات، شناسه...', 'Search user, description, ID...')}
                  value={searchQuery}
                  onChange={e => { setSearchQuery(e.target.value); setPage(1); }}
                  className="w-full pl-10 pr-4 py-2 bg-[var(--color-night-50)] border border-[var(--color-night-200)]/20 rounded-xl text-sm text-[var(--color-night-100)] focus:outline-none focus:ring-2 focus:ring-[var(--color-leaf-400)]"
                />
              </div>
              <select value={typeFilter} onChange={e => { setTypeFilter(e.target.value); setPage(1); }} className="px-3 py-2 bg-[var(--color-night-50)] border border-[var(--color-night-200)]/20 rounded-xl text-sm text-[var(--color-night-100)] focus:outline-none focus:ring-2 focus:ring-[var(--color-leaf-400)]">
                <option value="">{fa('همه انواع', 'All Types')}</option>
                <option value="payment">{fa('پرداخت', 'Payment')}</option>
                <option value="refund">{fa('بازپرداخت', 'Refund')}</option>
                <option value="payout">{fa('تسویه', 'Payout')}</option>
                <option value="fee">{fa('کارمزد', 'Fee')}</option>
                <option value="earn">{fa('برداشت', 'Earn')}</option>
                <option value="spend">{fa('خرید', 'Spend')}</option>
                <option value="transfer">{fa('انتقال', 'Transfer')}</option>
              </select>
              <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1); }} className="px-3 py-2 bg-[var(--color-night-50)] border border-[var(--color-night-200)]/20 rounded-xl text-sm text-[var(--color-night-100)] focus:outline-none focus:ring-2 focus:ring-[var(--color-leaf-400)]">
                <option value="">{fa('همه', 'All')}</option>
                <option value="pending">{fa('در انتظار', 'Pending')}</option>
                <option value="completed">{fa('تکمیل', 'Completed')}</option>
                <option value="failed">{fa('ناموفق', 'Failed')}</option>
                <option value="cancelled">{fa('لغو', 'Cancelled')}</option>
                <option value="refunded">{fa('بازپرداخت', 'Refunded')}</option>
              </select>
            </div>
          </Reveal>

          {/* Transactions Table */}
          <Reveal delay={0.2}>
            <div className="glass rounded-2xl overflow-hidden">
              {loading && page === 1 && <div className="p-8 text-center"><Loader2 className="h-8 w-8 animate-spin text-[var(--color-leaf-400)] mx-auto" /></div>}
              <div className="overflow-x-auto">
                <table className="w-full text-sm" dir="ltr">
                  <thead className="bg-[#f6ecd6]"><tr className="text-[var(--color-night-200)]/60 text-[11px] uppercase">
                    <th className="text-right p-3">{fa('شناسه', 'ID')}</th>
                    <th className="p-3">{fa('نوع', 'Type')}</th>
                    <th className="p-3">{fa('کاربر', 'User')}</th>
                    <th className="p-3">{fa('مبلغ', 'Amount')}</th>
                    <th className="p-3">{fa('وضعیت', 'Status')}</th>
                    <th className="p-3">{fa('توضیحات', 'Description')}</th>
                    <th className="p-3">{fa('سفارش/تسویه', 'Order/Settlement')}</th>
                    <th className="p-3">{fa('تاریخ', 'Date')}</th>
                    <th className="p-3">{fa('عملیات', 'Actions')}</th>
                  </tr></thead>
                  <tbody>
                    {transactions.length === 0 ? (
                      <tr><td colSpan={9} className="p-6 text-center text-[var(--color-night-200)]/50">{fa('تراکنشی یافت نشد', 'No transactions found')}</td></tr>
                    ) : transactions.map((t) => {
                      const typeInfo = getTypeInfo(t.type);
                      return (
                        <tr key={t.id} className="border-t border-white/5">
                          <td className="text-right p-3 font-mono text-xs text-[var(--color-night-200)]/70">{t.id.slice(0, 8)}...</td>
                          <td className="p-3">
                            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-[var(--color-night-50)] ${typeInfo.color}`}>
                              <typeInfo.icon className="h-3 w-3" /> {typeInfo.label}
                            </span>
                          </td>
                          <td className="p-3 text-[var(--color-night-200)]/70 text-xs">
                            <p className="font-medium text-[var(--color-night-100)]">{t.user_name || fa('نامشخص', 'Unknown')}</p>
                            <p>{t.user_email}</p>
                          </td>
                          <td className="p-3 font-mono text-sm text-[var(--color-night-100)]">{formatAmount(t.amount, t.currency)}</td>
                          <td className="p-3">{getStatusBadge(t.status)}</td>
                          <td className="p-3 text-[var(--color-night-200)]/70 text-xs max-w-xs truncate">{t.description}</td>
                          <td className="p-3 text-[var(--color-night-200)]/50 text-xs font-mono">
                            {t.related_order_id ? <span>{t.related_order_id.slice(0, 8)}...</span> : t.related_settlement_id ? <span className="text-purple-400">{t.related_settlement_id.slice(0, 8)}...</span> : <span>{fa('—', '—')}</span>}
                          </td>
                          <td className="p-3 text-xs text-[var(--color-night-200)]/60">{new Date(t.created_at).toLocaleString()}</td>
                          <td className="p-3">
                            <a href={`/dashboard/admin/transactions/${t.id}`} className="text-[var(--color-night-200)]/50 hover:text-[var(--color-leaf-400)]" title={fa('مشاهده', 'View')}>
                              <Eye className="h-4 w-4" />
                            </a>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {totalPages > 1 && (
                <div className="px-4 py-4 border-t border-white/10 flex items-center justify-between">
                  <p className="text-sm text-[var(--color-night-200)]/60">{fa('صفحه', 'Page')} {page} {fa('از', 'of')} {totalPages} ({totalCount} {fa('تراکنش', 'transactions')})</p>
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