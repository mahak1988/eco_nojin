import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useBilingual } from '../../hooks/useBilingual';
import { fetchOrderTracking } from '../../lib/marketplaceApi';
import Seo from '../../components/ui/Seo';
import PageHeader from '../../components/sections/PageHeader';
import Reveal from '../../components/ui/Reveal';
import { Loader2, CheckCircle, Clock, Truck, Package, XCircle, ArrowLeft } from 'lucide-react';

const STATUS_CONFIG = {
  pending: { icon: Clock, color: 'text-yellow-400', bg: 'bg-yellow-400/10' },
  confirmed: { icon: CheckCircle, color: 'text-blue-400', bg: 'bg-blue-400/10' },
  shipped: { icon: Truck, color: 'text-[var(--color-aqua-400)]', bg: 'bg-[var(--color-aqua-400)]/10' },
  delivered: { icon: Package, color: 'text-[var(--color-leaf-400)]', bg: 'bg-[var(--color-leaf-400)]/10' },
  cancelled: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-400/10' },
};

export default function OrderTrackingPage() {
  const { id } = useParams<{ id: string }>();
  const { fa, lang } = useBilingual();
  const isFa = lang === 'fa';
  const [tracking, setTracking] = useState<{
    order_id: string;
    order_number: string;
    current_status: string;
    timeline: Array<{
      timestamp: string;
      status: string;
      title: string;
      description: string;
    }>;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const loadTracking = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchOrderTracking(id);
        setTracking(data);
      } catch (err: any) {
        setError(err.message || 'خطا در بارگذاری ردیابی');
      } finally {
        setLoading(false);
      }
    };
    loadTracking();
  }, [id]);

  if (loading) {
    return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-leaf-400" /></div>;
  }

  if (error || !tracking) {
    return (
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-red-400">{error || fa('سفارش یافت نشد', 'Order not found')}</p>
          <Link to="/marketplace/orders" className="mt-4 inline-block text-[var(--color-leaf-400)]">{fa('بازگشت به سفارشات', 'Back to Orders')}</Link>
        </div>
      </div>
    );
  }

  const currentStatusConfig = STATUS_CONFIG[tracking.current_status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.pending;
  const CurrentIcon = currentStatusConfig.icon;

  return (
    <>
      <Seo title={fa('ردیابی سفارش', 'Order Tracking')} path={`/marketplace/orders/${id}/track`} />
      <PageHeader kicker={fa('ردیابی', 'Tracking')} title={`#${tracking.order_number}`} lead={fa('وضعیت و مکان فعلی سفارش', 'Current order status and location')} />
      <section className="px-4 py-10 sm:px-6" dir={isFa ? 'rtl' : 'ltr'}>
        <div className="mx-auto max-w-2xl">
          {/* Current Status Card */}
          <Reveal>
            <div className="glass rounded-3xl p-6 mb-6">
              <div className="flex items-center gap-4">
                <div className={`flex items-center justify-center h-16 w-16 rounded-2xl ${currentStatusConfig.bg}`}>
                  <CurrentIcon className={`h-8 w-8 ${currentStatusConfig.color}`} aria-hidden />
                </div>
                <div>
                  <p className="text-sm text-[var(--color-night-200)]/60">{fa('وضعیت فعلی', 'Current Status')}</p>
                  <p className="text-xl font-extrabold text-[var(--color-night-100)] capitalize">{tracking.current_status}</p>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between">
                <span className="text-sm text-[var(--color-night-200)]/60">{fa('شماره سفارش:', 'Order:')}</span>
                <span className="font-mono font-bold text-[var(--color-night-100)]">{tracking.order_number}</span>
              </div>
            </div>
          </Reveal>

          {/* Timeline */}
          <Reveal delay={0.05}>
            <div className="glass rounded-3xl p-6">
              <h3 className="mb-4 text-lg font-extrabold text-[var(--color-night-100)]">{fa('زمان‌بندی سفارش', 'Order Timeline')}</h3>
              <div className="relative">
                <div className="absolute start-4 top-0 bottom-0 w-0.5 bg-white/10" aria-hidden />
                {tracking.timeline.map((event, index) => {
                  const config = STATUS_CONFIG[event.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.pending;
                  const EventIcon = config.icon;
                  const isLast = index === tracking.timeline.length - 1;
                  const isCurrent = event.status === tracking.current_status;

                  return (
                    <div key={index} className="relative flex gap-4 pb-6 last:pb-0">
                      <div className="relative flex-shrink-0">
                        <div className={`flex items-center justify-center h-10 w-10 rounded-full ${config.bg} ${isCurrent ? 'ring-4 ring-[var(--color-night-950)]' : ''}`}>
                          <EventIcon className={`h-5 w-5 ${config.color}`} aria-hidden />
                        </div>
                        {!isLast && <div className="absolute start-4 top-10 bottom-0 w-0.5 bg-white/10" aria-hidden />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={`font-bold text-[var(--color-night-100)] ${isCurrent ? 'text-[var(--color-leaf-400)]' : ''}`}>{event.title}</p>
                        <p className="text-sm text-[var(--color-night-200)]/60 mt-0.5">{event.description}</p>
                        <p className="text-[11px] text-[var(--color-night-200)]/40 mt-1">
                          {new Date(event.timestamp).toLocaleString(isFa ? 'fa-IR' : 'en-US', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </Reveal>

          {/* Back Link */}
          <Reveal delay={0.1}>
            <Link to="/marketplace/orders" className="mt-6 inline-flex items-center gap-2 text-[var(--color-leaf-400)] hover:text-[var(--color-leaf-300)]">
              <ArrowLeft className="h-4 w-4" aria-hidden />
              {fa('بازگشت به سفارشات', 'Back to Orders')}
            </Link>
          </Reveal>
        </div>
      </section>
    </>
  );
}