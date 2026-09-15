import { Link } from 'react-router-dom';
import { useBilingual } from '../../hooks/useBilingual';
import { useMarketplace } from '../../context/MarketplaceContext';
import Seo from '../../components/ui/Seo';
import PageHeader from '../../components/sections/PageHeader';
import { Minus, Plus, Trash2, ShoppingBag } from 'lucide-react';

export default function CartPage() {
  const { fa } = useBilingual();
  const { cart, removeFromCart, updateCartItemQuantity } = useMarketplace();

  const subtotal = cart.items.reduce((sum, item) => {
    const price = typeof item === 'object' && 'price' in item ? (item as any).price || 0 : 0;
    return sum + (price as number) * (item.quantity || 0);
  }, 0);
  const platformFee = subtotal * 0.03;
  const landscapeFee = subtotal * 0.01;
  const total = subtotal + platformFee + landscapeFee;

  const handleQuantityChange = (productId: string, newQuantity: number) => {
    if (newQuantity < 1) {
      removeFromCart(productId);
    } else {
      updateCartItemQuantity(productId, newQuantity);
    }
  };

  return (
    <>
      <Seo title="سبد خرید" path="/marketplace/cart" />
      <PageHeader kicker="سبد خرید" title="سبد خرید" lead="محصولات انتخاب‌شده شما" />
      <section className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-4xl">
          {cart.items.length === 0 ? (
            <div className="glass rounded-3xl p-12 text-center">
              <ShoppingBag className="h-12 w-12 mx-auto mb-4 text-[var(--color-night-200)]/20" aria-hidden />
              <p className="text-[var(--color-night-200)]/60">{fa('سبد خرید شما خالی است', 'Your cart is empty')}</p>
              <Link to="/marketplace" className="mt-4 inline-block rounded-full bg-[var(--color-leaf-500)] px-6 py-2 text-sm font-extrabold text-[var(--color-night-950)]">{fa('مرور محصولات', 'Browse Products')}</Link>
            </div>
          ) : (
            <div className="flex flex-col gap-6">
              {cart.items.map((item: any) => (
                <div key={item.product_id} className="glass rounded-2xl p-4 flex items-center justify-between">
                  <div>
                    <p className="font-extrabold text-[var(--color-night-100)]">{item.product_name || item.product_id}</p>
                    <p className="text-xs text-[var(--color-night-200)]/60">{fa('تعداد:', 'Qty:')} {item.quantity}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleQuantityChange(item.product_id, (item.quantity || 1) - 1)}
                      disabled={item.quantity <= 1}
                      className="rounded-lg p-1.5 hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      <Minus className="h-4 w-4" />
                    </button>
                    <span className="w-8 text-center text-sm font-bold text-[var(--color-night-100)]">{item.quantity}</span>
                    <button
                      type="button"
                      onClick={() => handleQuantityChange(item.product_id, (item.quantity || 1) + 1)}
                      className="rounded-lg p-1.5 hover:bg-white/5"
                    >
                      <Plus className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => removeFromCart(item.product_id)}
                      className="rounded-lg p-1.5 hover:bg-red-400/10 hover:text-red-400"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
              <div className="glass rounded-2xl p-6 space-y-2">
                <div className="flex justify-between text-sm text-[var(--color-night-200)]/60"><span>{fa('زیرمجموعه', 'Subtotal')}</span><span>{subtotal.toLocaleString()} IRR</span></div>
                <div className="flex justify-between text-sm text-[var(--color-night-200)]/60"><span>{fa('کارمزد پلتفرم (3%)', 'Platform Fee')}</span><span>{platformFee.toFixed(0).toLocaleString()} IRR</span></div>
                <div className="flex justify-between text-sm text-[var(--color-night-200)]/60"><span>{fa('کارمزد منظر (1%)', 'Landscape Fee')}</span><span>{landscapeFee.toFixed(0).toLocaleString()} IRR</span></div>
                <div className="border-t border-white/10 pt-2 flex justify-between font-extrabold text-[var(--color-night-100)]"><span>{fa('جمع کل', 'Total')}</span><span>{total.toFixed(0).toLocaleString()} IRR</span></div>
                <Link to="/marketplace/checkout" className="mt-4 w-full inline-block rounded-xl bg-[var(--color-leaf-500)] px-6 py-3 text-center text-sm font-extrabold text-[var(--color-night-950)] transition hover:bg-[var(--color-leaf-400)]">{fa('پرداخت', 'Checkout')}</Link>
                <Link to="/marketplace" className="w-full inline-block rounded-xl border border-white/10 px-6 py-2 text-center text-xs font-bold text-[var(--color-night-200)]/70">{fa('ادامه خرید', 'Continue')}</Link>
              </div>
            </div>
          )}
        </div>
      </section>
    </>
  );
}
