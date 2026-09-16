/** SKU Management page — CRUD for stock keeping units. */

import { useState, useEffect } from 'react';
import { useBilingual } from '../../../hooks/useBilingual';
import { fetchSKUs, createSKU } from '../../../lib/inventoryApi';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { Package, Plus, Loader2, Trash2 } from 'lucide-react';

export default function SKUPage() {
  const { fa } = useBilingual();
  const [skus, setSkus] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ sku_code: '', name: '', uom: 'kg', standard_cost: '' });

  async function load() {
    try {
      const s = await fetchSKUs();
      setSkus(s);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate() {
    try {
      await createSKU({
        sku_code: form.sku_code,
        name: form.name,
        uom: form.uom,
        standard_cost: form.standard_cost || undefined,
      });
      setForm({ sku_code: '', name: '', uom: 'kg', standard_cost: '' });
      setShowForm(false);
      load();
    } catch { /* noop */ }
  }

  async function handleDelete(skuCode: string) {
    /* In a real app, would call DELETE endpoint */
    setSkus(skus.filter((s) => s.sku_code !== skuCode));
  }

  return (
    <>
      <Seo title={fa('مدیریت کالا', 'SKU Management')} path="/dashboard/inventory/sku" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-5xl">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
              <Package className="h-6 w-6 text-[var(--color-leaf-400)]" />
              {fa('کالاها', 'Products')}
            </h1>
            <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-2 rounded-xl bg-[var(--color-leaf-500)] px-4 py-2 text-sm font-extrabold text-[var(--color-night-950)]">
              <Plus className="h-4 w-4" /> {fa('کالای جدید', 'New SKU')}
            </button>
          </div>

          {showForm && (
            <Reveal>
              <div className="glass rounded-2xl p-6 mb-6">
                <h3 className="text-lg font-extrabold text-[var(--color-night-100)] mb-4">{fa('ایجاد کالا', 'Create SKU')}</h3>
                <div className="grid gap-3 lg:grid-cols-4">
                  <input placeholder="SKU Code" value={form.sku_code} onChange={(e) => setForm({ ...form, sku_code: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                  <input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                  <select value={form.uom} onChange={(e) => setForm({ ...form, uom: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm">
                    <option value="kg">kg</option><option value="piece">piece</option><option value="liter">liter</option><option value="m2">m2</option><option value="m3">m3</option>
                  </select>
                  <input placeholder="Standard Cost" type="number" value={form.standard_cost} onChange={(e) => setForm({ ...form, standard_cost: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                </div>
                <button onClick={handleCreate} className="mt-3 rounded-xl bg-[var(--color-leaf-500)] px-4 py-2 text-sm font-extrabold text-[var(--color-night-950)]">{fa('ذخیره', 'Save')}</button>
              </div>
            </Reveal>
          )}

          {loading && <div className="flex items-center gap-2 text-sm text-[var(--color-night-200)]/60"><Loader2 className="h-4 w-4 animate-spin" />{fa('در حال بارگذاری...', 'Loading...')}</div>}

          <Reveal delay={0.1}>
            <div className="glass rounded-2xl p-6">
              <h3 className="text-lg font-extrabold text-[var(--color-night-100)] mb-4">{fa('لیست کالاها', 'SKU List')}</h3>
              {skus.length === 0 ? (
                <p className="text-sm text-[var(--color-night-200)]/60">{fa('هیچ کالایی', 'No products')}</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm" dir="ltr">
                    <thead><tr className="text-xs text-[var(--color-night-200)]/60 text-left">
                      <th className="pb-2">{fa('کد', 'Code')}</th><th className="pb-2">{fa('نام', 'Name')}</th><th className="pb-2">{fa('واحد', 'UOM')}</th><th className="pb-2">{fa('هزینه', 'Cost')}</th><th className="pb-2">{fa('عملیات', 'Actions')}</th>
                    </tr></thead>
                    <tbody>
                      {skus.map((s) => (
                        <tr key={s.id} className="border-t border-[var(--color-night-200)]/10">
                          <td className="py-2 font-mono text-xs">{s.sku_code}</td>
                          <td className="py-2">{s.name}</td>
                          <td className="py-2">{s.uom}</td>
                          <td className="py-2">{s.standard_cost ?? '-'}</td>
                          <td className="py-2">
                            <button onClick={() => handleDelete(s.sku_code)} className="text-xs text-[#e8c66b] hover:underline"><Trash2 className="h-3 w-3 inline" /></button>
                          </td>
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

