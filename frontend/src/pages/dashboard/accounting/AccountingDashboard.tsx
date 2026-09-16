/** Accounting Dashboard — financial overview with key metrics. */

import { useState, useEffect } from 'react';
import { useBilingual } from '../../../hooks/useBilingual';
import { fetchOrders } from '../../../lib/commerceApi';
import { fetchWallet } from '../../../lib/financeApi';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { DollarSign, Loader2, TrendingUp } from 'lucide-react';

export default function AccountingDashboard() {
  const { fa } = useBilingual();
  const [orders, setOrders] = useState<any[]>([]);
  const [wallet, setWallet] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      const [o, w] = await Promise.all([
        fetchOrders({ limit: 50 }).catch(() => null),
        fetchWallet().catch(() => null),
      ]);
      if (o) setOrders(o.orders);
      if (w) setWallet(w);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const revenue = orders.reduce((sum, o) => sum + parseFloat(o.total || '0'), 0);
  const paidOrders = orders.filter((o) => o.payment_status === 'paid');
  const paidRevenue = paidOrders.reduce((sum, o) => sum + parseFloat(o.total || '0'), 0);

  return (
    <>
      <Seo title={fa('حسابداری', 'Accounting')} path="/dashboard/accounting" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-6xl">
          <h1 className="mb-6 text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
            <DollarSign className="h-6 w-6 text-[var(--color-leaf-400)]" />
            {fa('داشبورد حسابداری', 'Accounting Dashboard')}
          </h1>

          {loading && <div className="flex items-center gap-2 text-sm text-[var(--color-night-200)]/60"><Loader2 className="h-4 w-4 animate-spin" />{fa('در حال بارگذاری...', 'Loading...')}</div>}

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <Reveal>
              <div className="glass rounded-2xl p-4 text-center">
                <p className="text-3xl font-extrabold text-[var(--color-leaf-400)]">{revenue.toLocaleString()}</p>
                <p className="text-xs text-[var(--color-night-200)]/60">{fa('درآمد کل', 'Total Revenue')}</p>
              </div>
            </Reveal>
            <Reveal delay={0.07}>
              <div className="glass rounded-2xl p-4 text-center">
                <p className="text-3xl font-extrabold text-[var(--color-aqua-400)]">{paidRevenue.toLocaleString()}</p>
                <p className="text-xs text-[var(--color-night-200)]/60">{fa('درآمد پرداخت شده', 'Paid Revenue')}</p>
              </div>
            </Reveal>
            <Reveal delay={0.14}>
              <div className="glass rounded-2xl p-4 text-center">
                <p className="text-3xl font-extrabold text-[var(--color-amber-400)]">{paidOrders.length}</p>
                <p className="text-xs text-[var(--color-night-200)]/60">{fa('سفارشات پرداخت شده', 'Paid Orders')}</p>
              </div>
            </Reveal>
            <Reveal delay={0.21}>
              <div className="glass rounded-2xl p-4 text-center">
                <p className="text-3xl font-extrabold text-[var(--color-leaf-400)]">{wallet ? wallet.balance : '-'}</p>
                <p className="text-xs text-[var(--color-night-200)]/60">{fa('موجودی کیف', 'Wallet')}</p>
              </div>
            </Reveal>
          </div>

          <Reveal delay={0.28}>
            <div className="glass rounded-2xl p-6">
              <h3 className="flex items-center gap-2 text-base font-extrabold text-[var(--color-night-100)] mb-4">
                <TrendingUp className="h-5 w-5 text-[var(--color-leaf-400)]" />
                {fa('وضعیت مالی', 'Financial Status')}
              </h3>
              <div className="grid grid-cols-2 gap-4 text-sm" dir="ltr">
                <div className="text-[var(--color-night-200)]/60">{fa('درآمد کل', 'Revenue')}: {revenue.toFixed(2)} IRR</div>
                <div className="text-[var(--color-night-200)]/60">{fa('درآمد پرداخت شده', 'Paid')}: {paidRevenue.toFixed(2)} IRR</div>
                <div className="text-[var(--color-night-200)]/60">{fa('درصد دریافت', 'Collection')}: {revenue > 0 ? ((paidRevenue / revenue) * 100).toFixed(1) : 0}%</div>
                <div className="text-[var(--color-night-200)]/60">{fa('موجودی کل', 'Total Balance')}: {wallet ? wallet.balance : '-'} ECO</div>
              </div>
            </div>
          </Reveal>
        </div>
      </div>
    </>
  );
}


