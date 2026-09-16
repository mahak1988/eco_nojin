/** Commerce Settlements - Settlement management for sellers */

import { useState, useEffect } from 'react';
import { useBilingual } from '../../../hooks/useBilingual';
import { fetchSettlements } from '../../../lib/commerceApi';
import type { Settlement } from '../../../lib/commerceTypes';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { RotateCcw, Loader2, DollarSign, Clock, CheckCircle2, AlertCircle, Filter } from 'lucide-react';

export default function CommerceSettlementsPage() {
  const { fa } = useBilingual();
  const [settlements, setSettlements] = useState<Settlement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchSettlements();
      setSettlements(res);
    } catch (err: any) {
      setError(err.message || fa('خطا در بارگذاری', 'Failed to load'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [statusFilter]);

  const filteredSettlements = statusFilter ? settlements.filter(s => s.status === statusFilter) : settlements;
  const totalAmount = filteredSettlements.reduce((sum, s) => sum + Number(s.amount), 0);
  const pendingCount = filteredSettlements.filter(s => s.status === 'pending').length;
  const completedCount = filteredSettlements.filter(s => s.status === 'completed').length;

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-[var(--color-leaf-400)]" /></div>;
  if (error) return <div className="p-6 text-center text-red-400">{error}</div>;

  return (
    <>
      <Seo title={fa('مدیریت تسویه‌ها', 'Settlements Management')} path="/dashboard/commerce/settlements" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-7xl">
          <h1 className="mb-6 text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
            <RotateCcw className="h-6 w-6 text-[var(--color-leaf-400)]" />
            {fa('مدیریت تسویه‌ها', 'Settlements Management')}
          </h1>

          {/* Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <Reveal delay={0}><div className="glass rounded-2xl p-4 text-center"><p className="text-3xl font-extrabold text-[var(--color-leaf-400)]">{filteredSettlements.length}</p><p className="text-xs text-[var(--color-night-200)]/60">{fa('کل تسویه‌ها', 'Total Settlements')}</p></div></Reveal>
            <Reveal delay={0.07}><div className="glass rounded-2xl p-4 text-center"><p className="text-3xl font-extrabold text-[#e8c66b]">{pendingCount}</p><p className="text-xs text-[var(--color-night-200)]/60">{fa('در انتظار', 'Pending')}</p></div></Reveal>
            <Reveal delay={0.14}><div className="glass rounded-2xl p-4 text-center"><p className="text-3xl font-extrabold text-[var(--color-leaf-400)]">{completedCount}</p><p className="text-xs text-[var(--color-night-200)]/60">{fa('تکمیل شده', 'Completed')}</p></div></Reveal>
            <Reveal delay={0.21}><div className="glass rounded-2xl p-4 text-center"><p className="text-3xl font-extrabold text-[var(--color-night-100)]">{totalAmount.toLocaleString()}</p><p className="text-xs text-[var(--color-night-200)]/60">{fa('مبلغ کل', 'Total Amount')}</p></div></Reveal>
          </div>

          {/* Filter */}
          <Reveal delay={0.3}>
            <div className="glass rounded-2xl p-4 mb-6 flex flex-wrap items-center gap-3">
              <span className="text-sm font-medium text-[var(--color-night-200)]/80">{fa('فیلتر وضعیت:', 'Status:')}</span>
              <select
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value)}
                className="bg-[var(--color-night-50)] border border-[var(--color-night-200)]/20 rounded-xl px-4 py-2 text-sm text-[var(--color-night-100)] focus:outline-none focus:ring-2 focus:ring-[var(--color-leaf-400)]"
              >
                <option value="">{fa('همه', 'All')}</option>
                <option value="pending">{fa('در انتظار', 'Pending')}</option>
                <option value="completed">{fa('تکمیل شده', 'Completed')}</option>
                <option value="failed">{fa('ناموفق', 'Failed')}</option>
              </select>
            </div>
          </Reveal>

          {/* Settlements Table */}
          <Reveal delay={0.4}>
            <div className="glass rounded-2xl overflow-hidden">
              {loading && <div className="p-8 text-center"><Loader2 className="h-8 w-8 animate-spin text-[var(--color-leaf-400)] mx-auto" /></div>}
              <div className="overflow-x-auto">
                <table className="w-full text-sm" dir="ltr">
                  <thead className="bg-[#f6ecd6]"><tr className="text-[var(--color-night-200)]/60 text-[11px] uppercase">
                    <th className="text-right p-3">{fa('شناسه', 'ID')}</th>
                    <th className="p-3">{fa('سفارش', 'Order')}</th>
                    <th className="p-3">{fa('فروشنده', 'Seller')}</th>
                    <th className="p-3">{fa('مبلغ', 'Amount')}</th>
                    <th className="p-3">{fa('ارز', 'Currency')}</th>
                    <th className="p-3">{fa('وضعیت', 'Status')}</th>
                    <th className="p-3">{fa('بچ دفتری', 'Journal Batch')}</th>
                    <th className="p-3">{fa('تاریخ', 'Date')}</th>
                  </tr></thead>
                  <tbody>
                    {filteredSettlements.length === 0 ? (
                      <tr><td colSpan={8} className="p-6 text-center text-[var(--color-night-200)]/50">{fa('تسویه‌ای یافت نشد', 'No settlements found')}</td></tr>
                    ) : filteredSettlements.map((s) => (
                      <tr key={s.id} className="border-t border-white/5">
                        <td className="text-right p-3 font-mono text-xs">{s.id.slice(0, 20)}</td>
                        <td className="p-3 font-mono text-xs">{s.order_id.slice(0, 20)}</td>
                        <td className="p-3 text-[var(--color-night-200)]/70 text-xs">{s.seller_id.slice(0, 8)}...</td>
                        <td className="p-3 font-bold text-[var(--color-night-100)]">{Number(s.amount).toLocaleString()}</td>
                        <td className="p-3 text-[var(--color-night-200)]/70">{s.currency}</td>
                        <td className="p-3">
                          <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${s.status === 'completed' ? 'bg-[var(--color-leaf-500)]/20 text-[var(--color-leaf-400)]' : s.status === 'pending' ? 'bg-[#e8c66b]/20 text-[#e8c66b]' : 'bg-red-500/20 text-red-400'}`}>{s.status}</span>
                        </td>
                        <td className="p-3 text-[var(--color-night-200)]/70 font-mono text-xs">{s.journal_batch_id ? s.journal_batch_id.slice(0, 16) : '-'}</td>
                        <td className="p-3 text-xs text-[var(--color-night-200)]/60">{new Date(s.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </Reveal>
        </div>
      </div>
    </>
  );
}