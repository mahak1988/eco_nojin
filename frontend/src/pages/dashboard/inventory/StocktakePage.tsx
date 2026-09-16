/** Stocktakes page — create and approve stocktake sessions. */

import { useState, useEffect } from 'react';
import { useBilingual } from '../../../hooks/useBilingual';
import { fetchSKUs, createStocktake } from '../../../lib/inventoryApi';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { ClipboardList, Loader2 } from 'lucide-react';

export default function StocktakePage() {
  const { fa } = useBilingual();
  const [skus, setSkus] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ warehouse_id: '' });
  const [lines, setLines] = useState<Array<{ sku_id: number; counted_qty: string }>>([]);
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    try {
      const s = await fetchSKUs();
      setSkus(s);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  function addLine() {
    setLines([...lines, { sku_id: 0, counted_qty: '0' }]);
  }

  function updateLine(index: number, field: string, value: any) {
    const newLines = [...lines];
    newLines[index] = { ...newLines[index], [field]: value };
    setLines(newLines);
  }

  async function handleCreate() {
    setSubmitting(true);
    try {
      await createStocktake({
        warehouse_id: parseInt(form.warehouse_id),
        lines: lines.filter((l) => l.sku_id > 0).map((l) => ({
          sku_id: l.sku_id,
          counted_qty: l.counted_qty,
        })),
      });
      setLines([]);
      setShowForm(false);
    } catch { /* noop */ }
    setSubmitting(false);
  }

  return (
    <>
      <Seo title={fa('تعدادشماری', 'Stocktakes')} path="/dashboard/inventory/stocktakes" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-5xl">
          <h1 className="mb-6 text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
            <ClipboardList className="h-6 w-6 text-[var(--color-leaf-400)]" />
            {fa('تعدادشماری', 'Stocktakes')}
          </h1>

          {loading && <div className="flex items-center gap-2 text-sm text-[var(--color-night-200)]/60"><Loader2 className="h-4 w-4 animate-spin" />{fa('در حال بارگذاری...', 'Loading...')}</div>}

          <Reveal>
            <div className="glass rounded-2xl p-6 mb-6">
              <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-2 rounded-xl bg-[var(--color-leaf-500)] px-4 py-2 text-sm font-extrabold text-[var(--color-night-950)]">
                <ClipboardList className="h-4 w-4" /> {fa('تعدادشماری جدید', 'New Stocktake')}
              </button>

              {showForm && (
                <div className="mt-4">
                  <input placeholder="Warehouse ID" type="number" value={form.warehouse_id} onChange={(e) => setForm({ ...form, warehouse_id: e.target.value })} className="mb-3 rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                  <h4 className="text-sm font-extrabold text-[var(--color-night-100)] mb-2">{fa('خطوط', 'Lines')}</h4>
                  {lines.map((line, i) => (
                    <div key={i} className="flex gap-2 mb-2">
                      <select value={line.sku_id} onChange={(e) => updateLine(i, 'sku_id', parseInt(e.target.value))} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2 text-sm">
                        <option value={0}>Select SKU...</option>
                        {skus.map((s) => <option key={s.id} value={s.id}>{s.sku_code}</option>)}
                      </select>
                      <input type="number" placeholder="Counted" value={line.counted_qty} onChange={(e) => updateLine(i, 'counted_qty', e.target.value)} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2 text-sm w-32" />
                    </div>
                  ))}
                  <button onClick={addLine} className="text-xs text-[var(--color-leaf-400)] hover:underline mb-3">+ {fa('افزودن خط', 'Add Line')}</button>
                  <button onClick={handleCreate} disabled={submitting || !form.warehouse_id} className="rounded-xl bg-[var(--color-leaf-500)] px-4 py-2 text-sm font-extrabold text-[var(--color-night-950)] disabled:opacity-50">
                    {submitting && <Loader2 className="h-4 w-4 animate-spin inline" />}
                    {fa('ایجاد', 'Create')}
                  </button>
                </div>
              )}
            </div>
          </Reveal>
        </div>
      </div>
    </>
  );
}


