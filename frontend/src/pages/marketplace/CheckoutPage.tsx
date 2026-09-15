import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useBilingual } from '../../hooks/useBilingual';
import { useMarketplace } from '../../context/MarketplaceContext';
import { createOrder } from '../../lib/marketplaceApi';
import Seo from '../../components/ui/Seo';
import PageHeader from '../../components/sections/PageHeader';
import { CreditCard, Truck, CheckCircle, ArrowLeft, AlertCircle, Loader2, Radio, Circle } from 'lucide-react';

export default function CheckoutPage() {
  const { fa } = useBilingual();
  const { cart } = useMarketplace();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [orderNum, setOrderNum] = useState('');
  const [error, setError] = useState('');
  const [form, setForm] = useState({ name: '', phone: '', address: '', city: '', postal: '' });
  const [paymentMethod, setPaymentMethod] = useState<'wallet' | 'bank' | 'cod'>('wallet');

  const subtotal = cart.items.reduce((sum, item: any) => sum + ((item.price || 0) * (item.quantity || 0)), 0);
  const total = subtotal + subtotal * 0.03 + subtotal * 0.01;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const order = await createOrder({
        shipping_address: form,
        payment_method: paymentMethod,
      });
      setOrderNum(order.order_number || order.id);
      setSuccess(true);
    } catch (err: any) {
      setError(err.message || 'خطا');
    } finally {
      setLoading(false);
    }
  };

  const paymentOptions = [
    { value: 'wallet' as const, label: { fa: 'کیف پول', en: 'Wallet' }, icon: <Wallet className="h-4 w-4" /> },
    { value: 'bank' as const, label: { fa: 'انتقال بانکی', en: 'Bank Transfer' }, icon: <Building2 className="h-4 w-4" /> },
    { value: 'cod' as const, label: { fa: 'پرداخت نقدی', en: 'Cash on Delivery' }, icon: <Banknote className="h-4 w-4" /> },
  ] as const;

  return (
    <>
      <Seo title="پرداخت" path="/marketplace/checkout" />
      <PageHeader kicker="پرداخت" title="پرداخت سفارش" lead="تکمیل اطلاعات و پرداخت" />
      <section className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-4xl">
          {success ? (
            <div className="glass rounded-3xl p-10 text-center">
              <CheckCircle className="h-16 w-16 mx-auto mb-4 text-[var(--color-leaf-400)]" />
              <h2 className="text-xl font-extrabold text-[var(--color-night-100)]">{fa('سفارش با موفقیت ثبت شد', 'Order placed!')}</h2>
              <p className="mt-2 text-sm text-[var(--color-night-200)]/60">{fa('شماره سفارش:', 'Order:')} {orderNum}</p>
              <Link to="/marketplace/orders" className="mt-6 inline-block rounded-full bg-[var(--color-leaf-500)] px-6 py-2.5 text-sm font-extrabold text-[var(--color-night-950)]">{fa('مشاهده سفارشات', 'View Orders')}</Link>
            </div>
          ) : (
            <div className="grid gap-6 lg:grid-cols-2">
              <form onSubmit={handleSubmit} className="glass rounded-3xl p-6 space-y-4">
                <h3 className="text-base font-extrabold text-[var(--color-night-100)] flex items-center gap-2"><Truck className="h-5 w-5 text-[var(--color-leaf-400)]" />{fa('آدرس ارسال', 'Shipping')}</h3>
                {['name', 'phone', 'address', 'city', 'postal'].map((field) => (
                  <input
                    key={field}
                    type="text"
                    required
                    placeholder={fa({ name: 'نام و نام خانوادگی', phone: 'شماره تماس', address: 'آدرس', city: 'شهر', postal: 'کد پستی' }[field], { name: 'Full Name', phone: 'Phone', address: 'Address', city: 'City', postal: 'Postal Code' }[field])}
                    value={form[field as keyof typeof form]}
                    onChange={(e) => setForm({ ...form, [field]: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-[var(--color-night-100)] outline-none focus:border-[var(--color-leaf-400)]"
                  />
                ))}
                <h3 className="text-base font-extrabold text-[var(--color-night-100)] flex items-center gap-2"><CreditCard className="h-5 w-5 text-[var(--color-leaf-400)]" />{fa('روش پرداخت', 'Payment')}</h3>
                <div className="flex flex-col gap-2">
                  {paymentOptions.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setPaymentMethod(opt.value)}
                      className={`flex items-center gap-3 rounded-xl border p-3 text-sm font-bold transition ${
                        paymentMethod === opt.value
                          ? 'border-[var(--color-leaf-500)] bg-[var(--color-leaf-500)]/10 text-[var(--color-leaf-300)]'
                          : 'border-white/10 bg-white/5 text-[var(--color-night-200)]/70 hover:border-[var(--color-leaf-400)]/30'
                      }`}
                    >
                      <div className={`flex items-center justify-center h-8 w-8 rounded-lg ${
                        paymentMethod === opt.value
                          ? 'bg-[var(--color-leaf-500)] text-[var(--color-night-950)]'
                          : 'bg-white/5 text-[var(--color-night-200)]/50'
                      }`}>
                        {paymentMethod === opt.value ? <Radio className="h-4 w-4" /> : <Circle className="h-4 w-4" />}
                      </div>
                      <span>{fa(opt.label.fa, opt.label.en)}</span>
                    </button>
                  ))}
                </div>
                {error && <p className="flex items-center gap-2 text-sm text-red-400"><AlertCircle className="h-4 w-4" />{error}</p>}
                <button type="submit" disabled={loading} className="w-full rounded-xl bg-[var(--color-leaf-500)] px-6 py-3 text-sm font-extrabold text-[var(--color-night-950)] transition hover:bg-[var(--color-leaf-400)] disabled:opacity-50">
                  {loading ? <Loader2 className="h-5 w-5 mx-auto animate-spin" /> : fa('ثبت سفارش', 'Place Order')}
                </button>
                <Link to="/marketplace/cart" className="flex items-center gap-2 justify-center text-xs text-[var(--color-night-200)]/50 hover:text-[var(--color-leaf-400)]"><ArrowLeft className="h-3 w-3" />{fa('بازگشت به سبد', 'Back to Cart')}</Link>
              </form>
              <div className="glass rounded-3xl p-6 space-y-2">
                <h3 className="text-base font-extrabold text-[var(--color-night-100)]">{fa('خلاصه سفارش', 'Order Summary')}</h3>
                {cart.items.map((item: any, i: number) => (
                  <div key={i} className="flex justify-between text-sm text-[var(--color-night-200)]/60"><span>{item.product_name || 'Item'} × {item.quantity}</span><span>{((item.price||0) * (item.quantity||0)).toFixed(0).toLocaleString()} IRR</span></div>
                ))}
                <div className="flex justify-between text-sm text-[var(--color-night-200)]/60"><span>{fa('زیرمجموعه', 'Subtotal')}</span><span>{subtotal.toFixed(0).toLocaleString()} IRR</span></div>
                <div className="flex justify-between font-extrabold text-[var(--color-night-100)] border-t border-white/10 pt-2"><span>{fa('جمع کل', 'Total')}</span><span>{total.toFixed(0).toLocaleString()} IRR</span></div>
              </div>
            </div>
          )}
        </div>
      </section>
    </>
  );
}

// Icons for payment methods
function Wallet({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 12V7H5V7H5V17H21V12Z" />
      <path d="M3 5V19H21" />
    </svg>
  );
}

function Building2({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M22 21V11L12 2L2 11V21" />
      <path d="M6 15V21" />
      <path d="M10 15V21" />
      <path d="M14 15V21" />
      <path d="M18 15V21" />
    </svg>
  );
}

function Banknote({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <line x1="8" y1="10" x2="16" y2="10" />
      <line x1="12" y1="4" x2="12" y2="20" />
    </svg>
  );
}
