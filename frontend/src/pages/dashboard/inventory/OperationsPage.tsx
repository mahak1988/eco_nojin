/** Stock Operations page — receipt, issue, transfer, adjust, return, scrap. */

import { useState, useEffect } from 'react';
import { useBilingual } from '../../../hooks/useBilingual';
import { fetchSKUs, stockReceipt, stockIssue, stockTransfer, stockAdjust, stockReturn, stockScrap } from '../../../lib/inventoryApi';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { ArrowRight, Loader2, CheckCircle } from 'lucide-react';

type OperationType = 'receipt' | 'issue' | 'transfer' | 'adjust' | 'return' | 'scrap';

export default function OperationsPage() {
  const { fa } = useBilingual();
  const [skus, setSkus] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [opType, setOpType] = useState<OperationType>('receipt');
  const [form, setForm] = useState({
    sku_code: '', warehouse_id: '', qty: '', location_id: '',
    from_warehouse_id: '', to_warehouse_id: '', reason: '', reference_id: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  async function load() {
    try {
      const s = await fetchSKUs();
      setSkus(s);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleSubmit() {
    setSubmitting(true);
    try {
      const qty = form.qty;
      const whId = parseInt(form.warehouse_id);
      const data = { sku_code: form.sku_code, warehouse_id: whId, qty: qty, location_id: undefined, reference_id: undefined } as { sku_code: string; warehouse_id: number; qty: string; location_id?: number; reference_id?: string };
      if (form.location_id) data.location_id = parseInt(form.location_id);
      if (form.reference_id) data.reference_id = form.reference_id;

      switch (opType) {
        case 'receipt': await stockReceipt(data); break;
        case 'issue': await stockIssue({ sku_code: form.sku_code, warehouse_id: whId, qty, location_id: form.location_id ? parseInt(form.location_id) : undefined, reference_id: form.reference_id }); break;
        case 'transfer': await stockTransfer({ sku_code: form.sku_code, from_warehouse_id: parseInt(form.from_warehouse_id), to_warehouse_id: parseInt(form.to_warehouse_id), qty }); break;
        case 'adjust': await stockAdjust({ sku_code: form.sku_code, warehouse_id: whId, qty: form.qty, reason: form.reason }); break;
        case 'return': await stockReturn({ sku_code: form.sku_code, warehouse_id: whId, qty, location_id: form.location_id ? parseInt(form.location_id) : undefined, reference_id: form.reference_id }); break;
        case 'scrap': await stockScrap({ sku_code: form.sku_code, warehouse_id: whId, qty, reason: form.reason }); break;
      }
      setDone(true);
      setForm({ sku_code: '', warehouse_id: '', qty: '', location_id: '', from_warehouse_id: '', to_warehouse_id: '', reason: '', reference_id: '' });
      setTimeout(() => setDone(false), 2000);
    } catch { /* noop */ }
    setSubmitting(false);
  }

  return (
    <>
      <Seo title={fa('عملیات انبار', 'Stock Operations')} path="/dashboard/inventory/operations" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-5xl">
          <h1 className="mb-6 text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
            <ArrowRight className="h-6 w-6 text-[var(--color-leaf-400)]" />
            {fa('عملیات انبار', 'Stock Operations')}
          </h1>

          {loading && <div className="flex items-center gap-2 text-sm text-[var(--color-night-200)]/60"><Loader2 className="h-4 w-4 animate-spin" />{fa('در حال بارگذاری...', 'Loading...')}</div>}

          <Reveal delay={0.1}>
            <div className="glass rounded-2xl p-6 mb-6">
              <h3 className="text-lg font-extrabold text-[var(--color-night-100)] mb-4">{fa('نوع عملیات', 'Operation Type')}</h3>
              <div className="flex flex-wrap gap-2 mb-4">
                {(['receipt', 'issue', 'transfer', 'adjust', 'return', 'scrap'] as OperationType[]).map((t) => (
                  <button
                    key={t}
                    onClick={() => setOpType(t)}
                    className={`rounded-xl px-3 py-1.5 text-xs font-extrabold ${opType === t ? 'bg-[var(--color-leaf-500)] text-[var(--color-night-950)]' : 'glass'}`}
                  >
                    {fa({ receipt: 'رسید', issue: 'صادر', transfer: 'انتقال', adjust: 'تعدیل', return: 'برگشت', scrap: 'مخلف' }[t], t[0].toUpperCase() + t.slice(1))}
                  </button>
                ))}
              </div>

              <div className="grid gap-3 lg:grid-cols-3">
                <select value={form.sku_code} onChange={(e) => setForm({ ...form, sku_code: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm">
                  <option value="">{fa('انتخاب کالا', 'Select SKU')}</option>
                  {skus.map((s) => <option key={s.id} value={s.sku_code}>{s.sku_code} — {s.name}</option>)}
                </select>
                <input placeholder="Warehouse ID" type="number" value={form.warehouse_id} onChange={(e) => setForm({ ...form, warehouse_id: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                <input placeholder="Quantity" type="number" value={form.qty} onChange={(e) => setForm({ ...form, qty: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                <input placeholder="Location ID" type="number" value={form.location_id} onChange={(e) => setForm({ ...form, location_id: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                {opType === 'transfer' && (
                  <>
                    <input placeholder="From WH ID" type="number" value={form.from_warehouse_id} onChange={(e) => setForm({ ...form, from_warehouse_id: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                    <input placeholder="To WH ID" type="number" value={form.to_warehouse_id} onChange={(e) => setForm({ ...form, to_warehouse_id: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                  </>
                )}
                <input placeholder="Reason" value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                <input placeholder="Reference ID" value={form.reference_id} onChange={(e) => setForm({ ...form, reference_id: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
              </div>

              <button onClick={handleSubmit} disabled={submitting || !form.sku_code || !form.qty || !form.warehouse_id} className="mt-4 flex items-center gap-2 rounded-xl bg-[var(--color-leaf-500)] px-5 py-2.5 text-sm font-extrabold text-[var(--color-night-950)] disabled:opacity-50">
                {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                {fa('اجرا', 'Execute')}
                {done && <CheckCircle className="h-4 w-4 text-[var(--color-leaf-400)]" />}
              </button>
            </div>
          </Reveal>
        </div>
      </div>
    </>
  );
}



