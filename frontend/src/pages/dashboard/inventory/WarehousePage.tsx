/** Warehouse Management page. */

import { useState, useEffect } from 'react';
import { useBilingual } from '../../../hooks/useBilingual';
import { fetchWarehouses, createWarehouse } from '../../../lib/inventoryApi';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { Warehouse as WarehouseIcon, Plus, Loader2 } from 'lucide-react';

export default function WarehousePage() {
  const { fa } = useBilingual();
  const [warehouses, setWarehouses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ code: '', name: '', city: '' });

  async function load() {
    try {
      const w = await fetchWarehouses();
      setWarehouses(w);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate() {
    try {
      await createWarehouse({ code: form.code, name: form.name, city: form.city || undefined });
      setForm({ code: '', name: '', city: '' });
      setShowForm(false);
      load();
    } catch { /* noop */ }
  }

  return (
    <>
      <Seo title={fa('مدیریت انبار', 'Warehouses')} path="/dashboard/inventory/warehouse" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-5xl">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
              <WarehouseIcon className="h-6 w-6 text-[var(--color-leaf-400)]" />
              {fa('انبارها', 'Warehouses')}
            </h1>
            <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-2 rounded-xl bg-[var(--color-leaf-500)] px-4 py-2 text-sm font-extrabold text-[var(--color-night-950)]">
              <Plus className="h-4 w-4" /> {fa('انبار جدید', 'New Warehouse')}
            </button>
          </div>

          {showForm && (
            <Reveal>
              <div className="glass rounded-2xl p-6 mb-6">
                <h3 className="text-lg font-extrabold text-[var(--color-night-100)] mb-4">{fa('ایجاد انبار', 'Create Warehouse')}</h3>
                <div className="grid gap-3 lg:grid-cols-3">
                  <input placeholder="Code" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                  <input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                  <input placeholder="City" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                </div>
                <button onClick={handleCreate} className="mt-3 rounded-xl bg-[var(--color-leaf-500)] px-4 py-2 text-sm font-extrabold text-[var(--color-night-950)]">{fa('ذخیره', 'Save')}</button>
              </div>
            </Reveal>
          )}

          {loading && <div className="flex items-center gap-2 text-sm text-[var(--color-night-200)]/60"><Loader2 className="h-4 w-4 animate-spin" />{fa('در حال بارگذاری...', 'Loading...')}</div>}

          <Reveal delay={0.1}>
            <div className="glass rounded-2xl p-6">
              <h3 className="text-lg font-extrabold text-[var(--color-night-100)] mb-4">{fa('لیست انبارها', 'Warehouse List')}</h3>
              {warehouses.length === 0 ? (
                <p className="text-sm text-[var(--color-night-200)]/60">{fa('هیچ انباری', 'No warehouses')}</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm" dir="ltr">
                    <thead><tr className="text-xs text-[var(--color-night-200)]/60 text-left">
                      <th className="pb-2">{fa('کد', 'Code')}</th><th className="pb-2">{fa('نام', 'Name')}</th><th className="pb-2">{fa('شهر', 'City')}</th>
                    </tr></thead>
                    <tbody>
                      {warehouses.map((w) => (
                        <tr key={w.id} className="border-t border-[var(--color-night-200)]/10">
                          <td className="py-2 font-mono text-xs">{w.code}</td>
                          <td className="py-2">{w.name}</td>
                          <td className="py-2">{w.city ?? '-'}</td>
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

