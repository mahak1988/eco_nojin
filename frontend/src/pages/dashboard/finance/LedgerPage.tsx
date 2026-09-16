/** Ledger page — journal batches and entries. */

import { useState, useEffect } from 'react';
import { useBilingual } from '../../../hooks/useBilingual';
import { useAuth } from '../../../context/AuthContext';
import { fetchJournalEntries, createAccount } from '../../../lib/financeApi';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { BookOpen, Plus, Loader2 } from 'lucide-react';

export default function LedgerPage() {
  const { fa } = useBilingual();
  const { isAdmin } = useAuth();
  const [entries, setEntries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [newAccount, setNewAccount] = useState({ code: '', name: '', type: 'asset', currency: 'IRR' });

  async function load() {
    try {
      const e = await fetchJournalEntries().catch(() => []);
      if (e) setEntries(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCreateAccount() {
    try {
      await createAccount(newAccount);
      setNewAccount({ code: '', name: '', type: 'asset', currency: 'IRR' });
      setShowForm(false);
    } catch { /* noop */ }
  }

  return (
    <>
      <Seo title={fa('دفتر سهامداری', 'Ledger')} path="/dashboard/finance/ledger" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-5xl">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
              <BookOpen className="h-6 w-6 text-[var(--color-leaf-400)]" />
              {fa('دفتر سهامداری', 'Ledger')}
            </h1>
            {isAdmin && (
              <button
                onClick={() => setShowForm(!showForm)}
                className="flex items-center gap-2 rounded-xl bg-[var(--color-leaf-500)] px-4 py-2 text-sm font-extrabold text-[var(--color-night-950)]"
              >
                <Plus className="h-4 w-4" /> {fa('حساب جدید', 'New Account')}
              </button>
            )}
          </div>

          {showForm && (
            <Reveal>
              <div className="glass rounded-2xl p-6 mb-6">
                <h3 className="text-lg font-extrabold text-[var(--color-night-100)] mb-4">{fa('ایجاد حساب', 'Create Account')}</h3>
                <div className="grid gap-3 lg:grid-cols-4">
                  <input placeholder="Code" value={newAccount.code} onChange={(e) => setNewAccount({ ...newAccount, code: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                  <input placeholder="Name" value={newAccount.name} onChange={(e) => setNewAccount({ ...newAccount, name: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                  <select value={newAccount.type} onChange={(e) => setNewAccount({ ...newAccount, type: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm">
                    <option value="asset">Asset</option><option value="liability">Liability</option><option value="equity">Equity</option><option value="income">Income</option><option value="expense">Expense</option>
                  </select>
                  <input placeholder="Currency" value={newAccount.currency} onChange={(e) => setNewAccount({ ...newAccount, currency: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                </div>
                <button onClick={handleCreateAccount} className="mt-3 rounded-xl bg-[var(--color-leaf-500)] px-4 py-2 text-sm font-extrabold text-[var(--color-night-950)]">{fa('ذخیره', 'Save')}</button>
              </div>
            </Reveal>
          )}

          {loading ? (
            <div className="flex items-center gap-2 text-sm text-[var(--color-night-200)]/60"><Loader2 className="h-4 w-4 animate-spin" />{fa('در حال بارگذاری...', 'Loading...')}</div>
          ) : (
            <Reveal delay={0.1}>
              <div className="glass rounded-2xl p-6">
                <h3 className="text-lg font-extrabold text-[var(--color-night-100)] mb-4">{fa('معاونت‌ها', 'Journal Entries')}</h3>
                {entries.length === 0 ? (
                  <p className="text-sm text-[var(--color-night-200)]/60">{fa('هیچ معاونتی ثبت نشده', 'No entries')}</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm" dir="ltr">
                      <thead><tr className="text-xs text-[var(--color-night-200)]/60 text-left">
                        <th className="pb-2">{fa('بچ', 'Batch')}</th><th className="pb-2">{fa('نوع', 'Type')}</th><th className="pb-2">{fa('دارون', 'Asset')}</th><th className="pb-2">{fa('مبلغ', 'Amount')}</th><th className="pb-2">{fa('وضعیت', 'Status')}</th><th className="pb-2">{fa('توضیحات', 'Desc')}</th>
                      </tr></thead>
                      <tbody>
                        {entries.slice(0, 50).map((e, i) => (
                          <tr key={i} className="border-t border-[var(--color-night-200)]/10">
                            <td className="py-2 text-xs">{e.batch_id ?? '-'}</td>
                            <td className="py-2">{e.entry_type}</td>
                            <td className="py-2">{e.asset}</td>
                            <td className="py-2">{e.amount}</td>
                            <td className="py-2">{e.batch_id ? 'posted' : 'draft'}</td>
                            <td className="py-2 text-xs">{e.description ?? '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </Reveal>
          )}
        </div>
      </div>
    </>
  );
}



