import { Link } from 'react-router-dom';
import { ShoppingBag, Leaf, Droplets, BadgePercent, Star, Heart } from 'lucide-react';
import { useBilingual } from '../../hooks/useBilingual';
import { useMarketplace } from '../../context/MarketplaceContext';
import { CATEGORY_CONFIG } from './catalog-shared';
import type { Product } from '../../lib/marketplaceTypes';

interface ProductCardProps {
  product: Product;
  onAddToCart?: (product: Product) => void;
  adding?: boolean;
}

const CATEGORY_ICONS: Record<string, string> = {
  grains: '🌾',
  fruits: '🍎',
  vegetables: '🥬',
  dairy: '🥛',
  meat: '🥩',
  spices: '🫙',
  handicraft: '🧶',
  village: '🏘️',
  other: '📦',
};

export default function ProductCard({ product, onAddToCart, adding = false }: ProductCardProps) {
  const { fa, formatNumber } = useBilingual();
  const { isInWishlist, addToWishlist, removeFromWishlist } = useMarketplace();
  const catIcon = CATEGORY_ICONS[product.category] ?? '📦';
  const inWishlist = isInWishlist(product.id);

  const handleWishlistToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (inWishlist) {
      removeFromWishlist(product.id);
    } else {
      addToWishlist(product.id);
    }
  };

  return (
    <div className="glass glass-hover flex h-full flex-col overflow-hidden rounded-3xl transition-transform hover:-translate-y-1">
      <div className="relative aspect-[4/3] overflow-hidden bg-[var(--color-night-800)]">
        {product.images && product.images.length > 0 ? (
          <img
            src={product.images[0]}
            alt={product.name}
            className="h-full w-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-[var(--color-leaf-500)]/20 to-[var(--color-night-800)]">
            <span className="text-5xl" role="img" aria-label={product.category}>
              {catIcon}
            </span>
          </div>
        )}
        {product.organic_certified && (
          <span className="absolute left-3 top-3 inline-flex items-center gap-1.5 rounded-full bg-[var(--color-leaf-500)]/90 px-2.5 py-1 text-[10px] font-extrabold text-[var(--color-night-950)]">
            <Leaf className="h-3 w-3" aria-hidden />
            {fa('ارگانیک', 'Organic')}
          </span>
        )}
        {product.pgs_certified && (
          <span className="absolute right-3 top-3 inline-flex items-center gap-1.5 rounded-full bg-[var(--color-aqua-500)]/90 px-2.5 py-1 text-[10px] font-extrabold text-[var(--color-night-950)]">
            <BadgePercent className="h-3 w-3" aria-hidden />
            PGS
          </span>
        )}
        <button
          type="button"
          onClick={handleWishlistToggle}
          className={`absolute left-3 top-3 inline-flex items-center justify-center h-8 w-8 rounded-full transition-colors ${
            inWishlist
              ? 'bg-red-500/90 text-white'
              : 'bg-white/10 text-[var(--color-night-200)]/70 hover:bg-red-500/20 hover:text-red-400'
          }`}
          aria-label={inWishlist ? fa('حذف از علاقه‌مندی‌ها', 'Remove from wishlist') : fa('افزودن به علاقه‌مندی‌ها', 'Add to wishlist')}
        >
          <Heart className={`h-4 w-4 ${inWishlist ? 'fill-current' : ''}`} aria-hidden />
        </button>
      </div>

      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-base font-extrabold text-[var(--color-night-100)] line-clamp-2">
            {product.name}
          </h3>
          <span className="shrink-0 rounded-full bg-[var(--color-sand-500)]/10 px-2 py-1 text-[10px] font-bold text-[var(--color-sand-300)]">
            {catIcon} {CATEGORY_CONFIG[product.category] ? fa(CATEGORY_CONFIG[product.category].labelFa, CATEGORY_CONFIG[product.category].labelEn) : product.category}
          </span>
        </div>

        <p className="text-xs leading-6 text-[var(--color-night-200)]/55 line-clamp-2">
          {product.producer_name}
        </p>
        {product.description && (
          <p className="text-[11px] leading-5 text-[var(--color-night-200)]/40 line-clamp-2 italic">
            {product.description}
          </p>
        )}

        <div className="mt-auto flex items-end justify-between gap-2">
          <div>
            <p className="text-lg font-extrabold text-[var(--color-leaf-400)]">
              {formatNumber(product.price)} {fa('ریال/کیلوگرم', 'IRR/kg')}
            </p>
            <p className="text-[10px] text-[var(--color-night-200)]/40">
              {fa('کیلوگرم', 'kg')}
            </p>
          </div>
          <div className="flex flex-col items-end gap-1.5">
            <div className="flex items-center gap-1">
              <Star className="h-3 w-3 fill-[var(--color-sand-400)] text-[var(--color-sand-400)]" aria-hidden />
              <span className="text-[11px] font-bold text-[var(--color-night-200)]/70">
                {formatNumber(product.rating, { maximumFractionDigits: 1 })}
              </span>
            </div>
            {onAddToCart ? (
              <button
                type="button"
                onClick={() => onAddToCart(product)}
                disabled={adding || product.quantity_available <= 0}
                className="inline-flex items-center gap-1.5 rounded-full bg-[var(--color-leaf-500)] px-3 py-1.5 text-[10px] font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.05] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ShoppingBag className="h-3.5 w-3.5" aria-hidden />
                {adding ? fa('...', '...') : fa('افزودن', 'Add')}
              </button>
            ) : (
              <Link
                to={`/marketplace/products/${product.id}`}
                className="inline-flex items-center gap-1.5 rounded-full border border-[var(--color-leaf-500)]/40 bg-[var(--color-leaf-500)]/10 px-3 py-1.5 text-[10px] font-extrabold text-[var(--color-leaf-300)] transition-transform hover:scale-[1.05]"
              >
                {fa('نمایش', 'View')}
              </Link>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3 border-t border-[var(--color-night-700)]/60 pt-2 text-[10px] text-[var(--color-night-200)]/50">
          <span className="inline-flex items-center gap-1">
            <Droplets className="h-3 w-3" aria-hidden />
            {formatNumber(product.water_footprint_liters)}L
          </span>
          <span className="inline-flex items-center gap-1">
            <Leaf className="h-3 w-3" aria-hidden />
            {formatNumber(product.carbon_footprint_kg_co2)}kg CO₂
          </span>
        </div>
      </div>
    </div>
  );
}