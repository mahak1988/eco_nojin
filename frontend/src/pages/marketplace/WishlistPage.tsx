import { Link } from 'react-router-dom';
import { useBilingual } from '../../hooks/useBilingual';
import { useMarketplace } from '../../context/MarketplaceContext';
import ProductCard from './ProductCard';
import Seo from '../../components/ui/Seo';
import PageHeader from '../../components/sections/PageHeader';
import Reveal from '../../components/ui/Reveal';
import { Heart, Loader2 } from 'lucide-react';

export default function WishlistPage() {
  const { fa } = useBilingual();
  const { wishlist, wishlistLoading, addToCart } = useMarketplace();

  return (
    <>
      <Seo title="علاقه‌مندی‌ها" path="/marketplace/wishlist" />
      <PageHeader kicker="علاقه‌مندی‌ها" title="محصولات ذخیره‌شده" lead="محصولاتی که برای خرید بعد ذخیره کرده‌اید" />
      <section className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-6xl">
          {wishlistLoading ? (
            <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-leaf-400" /></div>
          ) : wishlist.length === 0 ? (
            <div className="glass rounded-3xl p-12 text-center">
              <Heart className="h-12 w-12 mx-auto mb-4 text-[var(--color-night-200)]/20" aria-hidden />
              <p className="text-[var(--color-night-200)]/60">{fa('لیست علاقه‌مندی‌ شما خالی است', 'Your wishlist is empty')}</p>
              <Link to="/marketplace" className="mt-4 inline-block rounded-full bg-[var(--color-leaf-500)] px-6 py-2 text-sm font-extrabold text-[var(--color-night-950)]">{fa('مرور محصولات', 'Browse Products')}</Link>
            </div>
          ) : (
            <div className="flex flex-col gap-6">
              <Reveal>
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
                  {wishlist.map((product) => (
                    <ProductCard
                      key={product.id}
                      product={product}
                      onAddToCart={(p) => addToCart([{ product_id: p.id, quantity: 1 }])}
                    />
                  ))}
                </div>
              </Reveal>
            </div>
          )}
        </div>
      </section>
    </>
  );
}