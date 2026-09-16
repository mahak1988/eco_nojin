/** Reservations page — stock reservations lifecycle. */

import { useState, useEffect } from 'react';
import { useBilingual } from '../../../hooks/useBilingual';
import { fetchMovements, reserveStock } from '../../../lib/inventoryApi';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { ClipboardList, Loader2 } from 'lucide-react';

export default function ReservationsPage() {
  const { fa } = useBilingual();
  const [movements, setMovements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ sku_code: '', warehouse_id: '', qty: '', reference_id: '' });
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    try {
      const m = await fetchMovements({ limit: 50 });
      setMovements(m);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleReserve() {
    setSubmitting(true);
    try {
      await reserveStock({
        sku_code: form.sku_code,
        warehouse_id: parseInt(form.warehouse_id),
        qty: form.qty,
        reference_type: 'order',
        reference_id: form.reference_id,
      });
      setForm({ sku_code: '', warehouse_id: '', qty: '', reference_id: '' });
      load();
    } catch { /* noop */ }
    setSubmitting(false);
  }

  return (
    <>
      <Seo title={fa('رزرو کالا', 'Reservations')} path="/dashboard/inventory/reservations" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-5xl">
          <h1 className="mb-6 text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
            <ClipboardList className="h-6 w-6 text-[var(--color-leaf-400)]" />
            {fa('رزروها', 'Reservations')}
          </h1>

          {loading && <div className="flex items-center gap-2 text-sm text-[var(--color-night-200)]/60"><Loader2 className="h-4 w-4 animate-spin" />{fa('در حال بارگذاری...', 'Loading...')}</div>}

          <Reveal>
            <div className="glass rounded-2xl p-6 mb-6">
              <h3 className="text-lg font-extrabold text-[var(--color-night-100)] mb-4">{fa('ایجاد رزرو', 'Create Reservation')}</h3>
              <div className="grid gap-3 lg:grid-cols-4">
                <input placeholder="SKU Code" value={form.sku_code} onChange={(e) => setForm({ ...form, sku_code: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                <input placeholder="Warehouse ID" type="number" value={form.warehouse_id} onChange={(e) => setForm({ ...form, warehouse_id: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                <input placeholder="Quantity" value={form.qty} onChange={(e) => setForm({ ...form, qty: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
                <input placeholder="Reference ID" value={form.reference_id} onChange={(e) => setForm({ ...form, reference_id: e.target.value })} className="rounded-xl border border-[var(--color-night-200)]/20 bg-[var(--color-night-900)] p-2.5 text-sm" />
              </div>
              <button onClick={handleReserve} disabled={submitting || !form.sku_code} className="mt-3 rounded-xl bg-[var(--color-leaf-500)] px-4 py-2 text-sm font-extrabold text-[var(--color-night-950)] disabled:opacity-50">{fa('رزرو', 'Reserve')}</button>
            </div>
          </Reveal>

          <Reveal delay={0.1}>
            <div className="glass rounded-2xl p-6">
              <h3 className="text-lg font-extrabold text-[var(--color-night-100)] mb-4">{fa('حرکات اخیر', 'Recent Movements')}</h3>
              {movements.length === 0 ? (
                <p className="text-sm text-[var(--color-night-200)]/60">{fa('هیچ حرکتی', 'No movements')}</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm" dir="ltr">
                    <thead><tr className="text-xs text-[var(--color-night-200)]/60 text-left">
                      <th className="pb-2">{fa('نوع', 'Type')}</th><th className="pb-2">{fa('کالا', 'SKU')}</th><th className="pb-2">{fa('مقدار', 'Qty')}</th><th className="pb-2">{fa('انبار', 'WH')}</th>
                    </tr></thead>
                    <tbody>
                      {movements.slice(0, 20).map((m, i) => (
                        <tr key={i} className="border-t border-[var(--color-night-200)]/10">
                          <td className="py-2">{m.movement_type}</td>
                          <td className="py-2">{m.sku_code ?? '-'}</td>
                          <td className="py-2">{m.qty}</td>
                          <td className="py-2">{m.warehouse_id ?? '-'}</td>
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


