/** Inventory Dashboard — stock overview, warehouses, recent movements. */

import { useState, useEffect } from 'react';
import { useBilingual } from '../../../hooks/useBilingual';
import { fetchSKUs, fetchWarehouses, fetchMovements } from '../../../lib/inventoryApi';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { Package, Warehouse, Activity, Loader2 } from 'lucide-react';

export default function InventoryDashboard() {
  const { fa } = useBilingual();
  const [skus, setSkus] = useState<any[]>([]);
  const [warehouses, setWarehouses] = useState<any[]>([]);
  const [movements, setMovements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      const [s, w, m] = await Promise.all([
        fetchSKUs().catch(() => []),
        fetchWarehouses().catch(() => []),
        fetchMovements({ limit: 10 }).catch(() => []),
      ]);
      setSkus(s); setWarehouses(w); setMovements(m);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <>
      <Seo title={fa('انبارداری', 'Inventory')} path="/dashboard/inventory" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-6xl">
          <h1 className="mb-6 text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
            <Package className="h-6 w-6 text-[var(--color-leaf-400)]" />
            {fa('انبارداری', 'Inventory')}
          </h1>

          {loading && (
            <div className="flex items-center gap-2 text-sm text-[var(--color-night-200)]/60">
              <Loader2 className="h-4 w-4 animate-spin" />
              {fa('در حال بارگذاری...', 'Loading...')}
            </div>
          )}

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <Reveal>
              <div className="glass rounded-2xl p-4 text-center">
                <p className="text-3xl font-extrabold text-[var(--color-leaf-400)]">{skus.length}</p>
                <p className="text-xs text-[var(--color-night-200)]/60">{fa('کالاها', 'SKUs')}</p>
              </div>
            </Reveal>
            <Reveal delay={0.07}>
              <div className="glass rounded-2xl p-4 text-center">
                <p className="text-3xl font-extrabold text-[var(--color-aqua-400)]">{warehouses.length}</p>
                <p className="text-xs text-[var(--color-night-200)]/60">{fa('انبارها', 'Warehouses')}</p>
              </div>
            </Reveal>
            <Reveal delay={0.14}>
              <div className="glass rounded-2xl p-4 text-center">
                <p className="text-3xl font-extrabold text-[var(--color-amber-400)]">{movements.length}</p>
                <p className="text-xs text-[var(--color-night-200)]/60">{fa('حرکات اخیر', 'Recent Movements')}</p>
              </div>
            </Reveal>
          </div>

          <div className="grid gap-4 lg:grid-cols-3 mb-8">
            <Reveal>
              <a href="#skus" className="glass glass-hover rounded-2xl p-6 block transition-all">
                <Package className="h-8 w-8 text-[var(--color-leaf-400)] mb-3" />
                <h3 className="text-base font-extrabold text-[var(--color-night-100)]">{fa('مدیریت کالا', 'SKUs')}</h3>
                <p className="mt-2 text-sm text-[var(--color-night-200)]/60">{fa('افزودن، ویرایش و حذف کالا', 'Manage products')}</p>
              </a>
            </Reveal>
            <Reveal delay={0.07}>
              <a href="#warehouses" className="glass glass-hover rounded-2xl p-6 block transition-all">
                <Warehouse className="h-8 w-8 text-[var(--color-aqua-400)] mb-3" />
                <h3 className="text-base font-extrabold text-[var(--color-night-100)]">{fa('مدیریت انبار', 'Warehouses')}</h3>
                <p className="mt-2 text-sm text-[var(--color-night-200)]/60">{fa('محل‌های ذخیره‌سازی', 'Storage locations')}</p>
              </a>
            </Reveal>
            <Reveal delay={0.14}>
              <a href="#operations" className="glass glass-hover rounded-2xl p-6 block transition-all">
                <Activity className="h-8 w-8 text-[var(--color-amber-400)] mb-3" />
                <h3 className="text-base font-extrabold text-[var(--color-night-100)]">{fa('عملیات انبار', 'Operations')}</h3>
                <p className="mt-2 text-sm text-[var(--color-night-200)]/60">{fa('رسید، صادر، انتقال', 'Receipt, issue, transfer')}</p>
              </a>
            </Reveal>
          </div>

          {/* Recent Movements */}
          <Reveal delay={0.21}>
            <div id="movements" className="glass rounded-2xl p-6">
              <h3 className="flex items-center gap-2 text-base font-extrabold text-[var(--color-night-100)] mb-4">
                <Activity className="h-5 w-5 text-[var(--color-leaf-400)]" />
                {fa('حرکات اخیر', 'Recent Movements')}
              </h3>
              {movements.length === 0 ? (
                <p className="text-sm text-[var(--color-night-200)]/60">{fa('هیچ حرکتی', 'No movements')}</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm" dir="ltr">
                    <thead><tr className="text-xs text-[var(--color-night-200)]/60 text-left">
                      <th className="pb-2">{fa('نوع', 'Type')}</th><th className="pb-2">{fa('کالا', 'SKU')}</th><th className="pb-2">{fa('مقدار', 'Qty')}</th><th className="pb-2">{fa('انبار', 'WH')}</th>
                    </tr></thead>
                    <tbody>
                      {movements.map((m, i) => (
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


