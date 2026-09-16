/** Accounting Journal page — view journal entries and account balances. */

import { useState, useEffect } from 'react';
import { useBilingual } from '../../../hooks/useBilingual';
import { fetchJournalEntries, fetchAccountBalance, fetchAccounts } from '../../../lib/financeApi';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { BookOpen, Loader2 } from 'lucide-react';

export default function JournalPage() {
  const { fa } = useBilingual();
  const [entries, setEntries] = useState<any[]>([]);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      const [e, a] = await Promise.all([
        fetchJournalEntries().catch(() => []),
        fetchAccounts().catch(() => []),
      ]);
      setEntries(e);
      setAccounts(a);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function loadBalance(accountId: string) {
    try {
      const result = await fetchAccountBalance(accountId);
      alert(`${fa('موجودی حساب', 'Account Balance')}: ${result.balance} ${result.asset}`);
    } catch { /* noop */ }
  }

  return (
    <>
      <Seo title={fa('دفتر سهامداری', 'Journal')} path="/dashboard/accounting/journal" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-5xl">
          <h1 className="mb-6 text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
            <BookOpen className="h-6 w-6 text-[var(--color-leaf-400)]" />
            {fa('دفتر سهامداری', 'Journal')}
          </h1>

          {loading && <div className="flex items-center gap-2 text-sm text-[var(--color-night-200)]/60"><Loader2 className="h-4 w-4 animate-spin" />{fa('در حال بارگذاری...', 'Loading...')}</div>}

          {/* Accounts summary */}
          <Reveal delay={0.07}>
            <div className="glass rounded-2xl p-6 mb-6">
              <h3 className="text-lg font-extrabold text-[var(--color-night-100)] mb-4">{fa('حساب‌ها', 'Accounts')}</h3>
              {accounts.length === 0 ? (
                <p className="text-sm text-[var(--color-night-200)]/60">{fa('هیچ حسابی', 'No accounts')}</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {accounts.map((acc) => (
                    <button
                      key={acc.id}
                      onClick={() => loadBalance(String(acc.id))}
                      className="rounded-xl bg-[var(--color-night-900)] px-3 py-1.5 text-xs font-extrabold text-[var(--color-night-100)] hover:bg-[var(--color-leaf-500)]/20"
                    >
                      {acc.code} — {acc.name}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </Reveal>

          <Reveal delay={0.14}>
            <div className="glass rounded-2xl p-6">
              <h3 className="text-lg font-extrabold text-[var(--color-night-100)] mb-4">{fa('معاونت‌ها', 'Journal Entries')}</h3>
              {entries.length === 0 ? (
                <p className="text-sm text-[var(--color-night-200)]/60">{fa('هیچ معاونتی', 'No entries')}</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm" dir="ltr">
                    <thead><tr className="text-xs text-[var(--color-night-200)]/60 text-left">
                      <th className="pb-2">{fa('بچ', 'Batch')}</th><th className="pb-2">{fa('حساب', 'Account')}</th><th className="pb-2">{fa('نوع', 'Type')}</th><th className="pb-2">{fa('دارون', 'Asset')}</th><th className="pb-2">{fa('مبلغ', 'Amount')}</th>
                    </tr></thead>
                    <tbody>
                      {entries.slice(0, 50).map((e, i) => (
                        <tr key={i} className="border-t border-[var(--color-night-200)]/10">
                          <td className="py-2 text-xs">{e.batch_id ?? '-'}</td>
                          <td className="py-2">{e.account_id}</td>
                          <td className="py-2">{e.entry_type}</td>
                          <td className="py-2">{e.asset}</td>
                          <td className="py-2">{e.amount}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </Reveal>
        </div>
      </div>
    </>
  );
}


