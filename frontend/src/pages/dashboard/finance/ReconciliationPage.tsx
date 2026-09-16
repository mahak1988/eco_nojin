/** Reconciliation page — wallet-ledger and full reconciliation. */

import { useState } from 'react';
import { useBilingual } from '../../../hooks/useBilingual';
import { useAuth } from '../../../context/AuthContext';
import { reconcileWalletLedger, fullReconciliation } from '../../../lib/financeApi';
import type { ReconciliationResult } from '../../../lib/financeTypes';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { RefreshCw, Loader2, CheckCircle, AlertTriangle } from 'lucide-react';

export default function ReconciliationPage() {
  const { fa } = useBilingual();
  const { isAdmin } = useAuth();
  const [result, setResult] = useState<ReconciliationResult | null>(null);
  const [mode, setMode] = useState<'wallet' | 'full'>('wallet');
  const [loading, setLoading] = useState(false);

  async function runReconciliation() {
    setLoading(true);
    try {
      const r = mode === 'wallet'
        ? await reconcileWalletLedger()
        : await fullReconciliation();
      setResult(r);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Seo title={fa('تطبیق', 'Reconciliation')} path="/dashboard/finance/reconciliation" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-3xl">
          <h1 className="mb-6 text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
            <RefreshCw className="h-6 w-6 text-[var(--color-leaf-400)]" />
            {fa('تطبیق حسابداری', 'Reconciliation')}
          </h1>

          {!isAdmin && (
            <div className="glass rounded-2xl p-6 text-[#e8c66b] text-sm mb-6">{fa('فقط مدیران قابلیت تطبیق دارند', 'Only admins can run reconciliation')}</div>
          )}

          <Reveal>
            <div className="glass rounded-2xl p-6 mb-6">
              <h3 className="text-lg font-extrabold text-[var(--color-night-100)] mb-4">{fa('انتخاب نوع تطبیق', 'Select Type')}</h3>
              <div className="flex gap-3 mb-4">
                <button
                  onClick={() => { setMode('wallet'); setResult(null); }}
                  className={`rounded-xl px-4 py-2 text-sm font-extrabold ${mode === 'wallet' ? 'bg-[var(--color-leaf-500)] text-[var(--color-night-950)]' : 'glass'}`}
                >
                  {fa('کیف ↔ دفتر', 'Wallet ↔ Ledger')}
                </button>
                <button
                  onClick={() => { setMode('full'); setResult(null); }}
                  className={`rounded-xl px-4 py-2 text-sm font-extrabold ${mode === 'full' ? 'bg-[var(--color-aqua-400)] text-[var(--color-night-950)]' : 'glass'}`}
                >
                  {fa('تطبیق کامل', 'Full Reconciliation')}
                </button>
              </div>
              <button
                onClick={runReconciliation}
                disabled={loading || !isAdmin}
                className="flex items-center gap-2 rounded-xl bg-[var(--color-leaf-500)] px-5 py-2.5 text-sm font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-105 disabled:opacity-50"
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                {fa('اجرای تطبیق', 'Run Reconciliation')}
              </button>
            </div>
          </Reveal>

          {result && (
            <Reveal delay={0.1}>
              <div className="glass rounded-2xl p-6">
                <h3 className="flex items-center gap-2 text-lg font-extrabold text-[var(--color-night-100)] mb-4">
                  {result.overall_ok ? <CheckCircle className="h-5 w-5 text-[var(--color-leaf-400)]" /> : <AlertTriangle className="h-5 w-5 text-[#e8c66b]" />}
                  {fa('نتیجه', 'Result')}
                </h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="text-[var(--color-night-200)]/60">{fa('تعداد بررسی', 'Checked')}: {result.total_checked}</div>
                  <div className="text-[var(--color-night-200)]/60">{fa('اختلافات', 'Discrepancies')}: {result.discrepancies_count}</div>
                  <div className="col-span-2">
                    {result.overall_ok ? (
                      <span className="text-[var(--color-leaf-400)] font-bold">{fa('کلیه تطبیق‌ها درست هستند ✓', 'All OK ✓')}</span>
                    ) : (
                      <span className="text-[#e8c66b] font-bold">{fa('بررسی اختلافات لازم است', 'Action needed')}</span>
                    )}
                  </div>
                  {result.discrepancies && Array.isArray(result.discrepancies) && result.discrepancies.length > 0 && (
                    <div className="col-span-2 mt-4">
                      <p className="text-xs text-[var(--color-night-200)]/60 mb-2">{fa('جزئیات اختلافات', 'Details')}:</p>
                      <pre className="rounded-xl bg-[var(--color-night-900)] p-4 text-xs overflow-x-auto">{JSON.stringify(result.discrepancies, null, 2)}</pre>
                    </div>
                  )}
                </div>
              </div>
            </Reveal>
          )}
        </div>
      </div>
    </>
  );
}


