import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useBilingual } from '../../hooks/useBilingual';
import { useMarketplace } from '../../context/MarketplaceContext';
import { fetchProducts, searchProducts } from '../../lib/marketplaceApi';
import ProductCard from './ProductCard';
import { CATEGORY_CONFIG } from './catalog-shared';
import type { Product, MarketplaceCategory } from '../../lib/marketplaceTypes';
import Seo from '../../components/ui/Seo';
import PageHeader from '../../components/sections/PageHeader';
import Reveal from '../../components/ui/Reveal';
import { Search, SlidersHorizontal, ShoppingBag, ChevronDown, ArrowUpDown } from 'lucide-react';

const PAGE_SIZE = 12;

const SORT_OPTIONS = [
  { value: 'price_asc', fa: 'قیمت: کم به زیاد', en: 'Price: Low to High' },
  { value: 'price_desc', fa: 'قیمت: زیاد به کم', en: 'Price: High to Low' },
  { value: 'rating', fa: 'امتیاز', en: 'Rating' },
  { value: 'newest', fa: 'جدیدترین', en: 'Newest' },
];

function mapSearchResults(results: Array<{ id: string; name: string; price_per_kg: number }>): Product[] {
  return results.map((r) => ({
    id: r.id,
    name: r.name,
    slug: '',
    category: 'other',
    description: '',
    price: r.price_per_kg,
    quantity_available: 0,
    minimum_order: 0,
    organic_certified: false,
    carbon_footprint_kg_co2: 0,
    water_footprint_liters: 0,
    producer_name: '',
    producer_id: '',
    origin_location: '',
    harvest_date: null,
    batch_number: '',
    traceability_code: '',
    pgs_certified: false,
    status: 'pending',
    images: [],
    tags: [],
    rating: 0,
    review_count: 0,
  }));
}

export default function CatalogPage() {
  const { fa, isFa } = useBilingual();
  const { cart } = useMarketplace();
  const [searchParams] = useSearchParams();

  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<MarketplaceCategory | 'all'>('all');
  const [organicOnly, setOrganicOnly] = useState(false);
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [sortBy, setSortBy] = useState('newest');
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  const loadProducts = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      if (searchQuery.trim()) {
        const result = await searchProducts(searchQuery.trim());
        setProducts(mapSearchResults(result.results));
        setHasMore(false);
      } else {
        const params: {
          category?: MarketplaceCategory;
          organic_only?: boolean;
          min_price?: number;
          max_price?: number;
          sort?: 'price_asc' | 'price_desc' | 'rating' | 'newest';
          limit?: number;
          offset?: number;
        } = {
          limit: PAGE_SIZE,
          offset,
          sort: sortBy as 'price_asc' | 'price_desc' | 'rating' | 'newest',
        };
        if (activeCategory !== 'all') {
          params.category = activeCategory;
        }
        if (organicOnly) {
          params.organic_only = true;
        }
        if (minPrice) {
          params.min_price = Number(minPrice);
        }
        if (maxPrice) {
          params.max_price = Number(maxPrice);
        }

        const data = await fetchProducts(params);
        setProducts(data.products);
        setHasMore(data.count > offset + data.products.length);
      }
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, activeCategory, organicOnly, minPrice, maxPrice, sortBy, offset]);

  useEffect(() => {
    const urlQuery = searchParams.get('q');
    if (urlQuery) {
      setSearchQuery(urlQuery);
    }
  }, [searchParams]);

  useEffect(() => {
    const timer = setTimeout(() => {
      loadProducts();
    }, 300);
    return () => clearTimeout(timer);
  }, [loadProducts]);

  const handleSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      setOffset(0);
      setSearchQuery(e.currentTarget.value);
    }
  };

  const handleCategoryChange = (category: MarketplaceCategory | 'all') => {
    setActiveCategory(category);
    setOffset(0);
  };

  const handleOrganicToggle = () => {
    setOrganicOnly((prev) => !prev);
    setOffset(0);
  };

  const handleMinPriceChange = (value: string) => {
    setMinPrice(value);
    setOffset(0);
  };

  const handleMaxPriceChange = (value: string) => {
    setMaxPrice(value);
    setOffset(0);
  };

  const handleSortChange = (value: string) => {
    setSortBy(value);
    setOffset(0);
  };

  const handleShowMore = () => {
    setOffset((prev) => prev + PAGE_SIZE);
  };

  const handleRetry = () => {
    setError(false);
    loadProducts();
  };

  const categories = [
    { key: 'all' as const, fa: 'همه', en: 'All' },
    ...(Object.keys(CATEGORY_CONFIG) as MarketplaceCategory[]).map((key) => ({
      key,
      fa: CATEGORY_CONFIG[key].labelFa,
      en: CATEGORY_CONFIG[key].labelEn,
    })),
  ];


  return (
    <>
      <Seo title="بازارگاه محلی اکو نوژین" path="/marketplace" />
      <PageHeader
        kicker="بازارگاه"
        title="کاتالوگ محصولات"
        lead="مجموعه کامل محصولات کشاورزان محلی با قیمت شفاف"
      />

      <section className="px-4 pb-10 sm:px-6" dir={isFa ? 'rtl' : 'ltr'}>
        <div className="mx-auto flex max-w-6xl flex-col gap-6">
          {/* Search bar */}
          <Reveal>
            <div className="relative mx-auto max-w-xl">
              <Search
                className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]/40"
                aria-hidden
              />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={handleSearchKeyDown}
                placeholder={fa('جستجو محصول...', 'Search products...')}
                className="w-full rounded-2xl border border-[var(--color-night-700)]/40 bg-[var(--color-night-800)]/60 py-2.5 pl-10 pr-4 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)]/30 focus:border-[var(--color-leaf-500)]/50 focus:outline-none"
              />
            </div>
          </Reveal>

          {/* Category chips */}
          <Reveal delay={0.03}>
            <div className="flex flex-wrap gap-2">
              {categories.map((cat) => (
                <button
                  key={cat.key}
                  type="button"
                  onClick={() => handleCategoryChange(cat.key)}
                  className={`inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[11px] font-bold transition-colors ${
                    activeCategory === cat.key
                      ? 'bg-[var(--color-leaf-500)] text-[var(--color-night-950)]'
                      : 'border border-[var(--color-night-700)]/40 bg-[var(--color-night-800)]/40 text-[var(--color-night-200)]/70 hover:border-[var(--color-leaf-500)]/30'
                  }`}
                >
                  {fa(cat.fa, cat.en)}
                </button>
              ))}
            </div>
          </Reveal>

          {/* Filter bar */}
          <Reveal delay={0.05}>
            <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-[var(--color-night-700)]/30 bg-[var(--color-night-800)]/40 p-3">
              <div className="flex items-center gap-1.5 text-[11px] font-bold text-[var(--color-night-200)]/50">
                <SlidersHorizontal className="h-3.5 w-3.5" aria-hidden />
                {fa('فیلترها', 'Filters')}
              </div>

              <label className="flex cursor-pointer items-center gap-1.5 rounded-full border border-[var(--color-night-700)]/40 px-3 py-1.5 text-[11px] font-bold text-[var(--color-night-200)]/70 transition-colors hover:border-[var(--color-leaf-500)]/30">
                <input
                  type="checkbox"
                  checked={organicOnly}
                  onChange={handleOrganicToggle}
                  className="h-3.5 w-3.5 accent-[var(--color-leaf-500)]"
                />
                {fa('ارگانیک', 'Organic')}
              </label>

              <div className="flex items-center gap-1">
                <input
                  type="number"
                  min={0}
                  placeholder={fa('از', 'Min')}
                  value={minPrice}
                  onChange={(e) => handleMinPriceChange(e.target.value)}
                  className="w-20 rounded-lg border border-[var(--color-night-700)]/40 bg-[var(--color-night-800)]/60 px-2 py-1.5 text-[11px] text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)]/30 focus:border-[var(--color-leaf-500)]/50 focus:outline-none"
                />
                <span className="text-[var(--color-night-200)]/30">—</span>
                <input
                  type="number"
                  min={0}
                  placeholder={fa('تا', 'Max')}
                  value={maxPrice}
                  onChange={(e) => handleMaxPriceChange(e.target.value)}
                  className="w-20 rounded-lg border border-[var(--color-night-700)]/40 bg-[var(--color-night-800)]/60 px-2 py-1.5 text-[11px] text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)]/30 focus:border-[var(--color-leaf-500)]/50 focus:outline-none"
                />
              </div>

              <div className="relative">
                <select
                  value={sortBy}
                  onChange={(e) => handleSortChange(e.target.value)}
                  className="appearance-none rounded-lg border border-[var(--color-night-700)]/40 bg-[var(--color-night-800)]/60 py-1.5 pl-3 pr-8 text-[11px] font-bold text-[var(--color-night-200)]/70 focus:border-[var(--color-leaf-500)]/50 focus:outline-none"
                >
                  {SORT_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {fa(opt.fa, opt.en)}
                    </option>
                  ))}
                </select>
                <ChevronDown
                  className="pointer-events-none absolute right-2 top-1/2 h-3 w-3 -translate-y-1/2 text-[var(--color-night-200)]/50"
                  aria-hidden
                />
                <ArrowUpDown
                  className="pointer-events-none absolute right-5 top-1/2 h-3 w-3 -translate-y-1/2 text-[var(--color-night-200)]/30"
                  aria-hidden
                />
              </div>

              {cart.total_items > 0 && (
                <div className="ml-auto flex items-center gap-1.5 rounded-full bg-[var(--color-leaf-500)]/15 px-3 py-1.5 text-[11px] font-bold text-[var(--color-leaf-300)]">
                  <ShoppingBag className="h-3 w-3" aria-hidden />
                  {cart.total_items}
                </div>
              )}
            </div>
          </Reveal>

          {/* Loading state */}
          {loading && (
            <Reveal delay={0.06}>
              <div className="flex flex-col items-center gap-3 py-16">
                <div className="h-10 w-10 animate-spin rounded-full border-2 border-[var(--color-leaf-500)]/25 border-t-[var(--color-leaf-400)]" />
                <p className="text-sm text-[var(--color-night-200)]/60">
                  {fa('در حال بارگذاری...', 'Loading...')}
                </p>
              </div>
            </Reveal>
          )}

          {/* Error state */}
          {!loading && error && (
            <Reveal delay={0.06}>
              <div className="flex flex-col items-center gap-3 py-16">
                <p className="text-base font-bold text-[var(--color-red-400)]">
                  {fa('خطا در بارگذاری', 'Error loading')}
                </p>
                <button
                  type="button"
                  onClick={handleRetry}
                  className="rounded-full bg-[var(--color-leaf-500)] px-5 py-2 text-xs font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.03]"
                >
                  {fa('تلاش دوباره', 'Retry')}
                </button>
              </div>
            </Reveal>
          )}

          {/* Empty state */}
          {!loading && !error && products.length === 0 && (
            <Reveal delay={0.06}>
              <div className="flex flex-col items-center gap-3 py-16">
                <p className="text-base text-[var(--color-night-200)]/60">
                  {fa('هیچ محصولی یافت نشد', 'No products found')}
                </p>
              </div>
            </Reveal>
          )}

          {/* Product grid */}
          {!loading && !error && products.length > 0 && (
            <>
              <Reveal delay={0.06}>
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
                  {products.map((product) => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </div>
              </Reveal>

              {/* Pagination */}
              {hasMore && (
                <Reveal delay={0.08}>
                  <div className="flex justify-center pt-4">
                    <button
                      type="button"
                      onClick={handleShowMore}
                      disabled={loading}
                      className="inline-flex items-center gap-2 rounded-full border border-[var(--color-leaf-500)]/40 bg-[var(--color-leaf-500)]/10 px-6 py-2.5 text-xs font-extrabold text-[var(--color-leaf-300)] transition-transform hover:scale-[1.03] disabled:opacity-50"
                    >
                      {fa('نمایش بیشتر', 'Show More')}
                      {loading && (
                        <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-[var(--color-leaf-500)]/30 border-t-[var(--color-leaf-300)]" />
                      )}
                    </button>
                  </div>
                </Reveal>
              )}
            </>
          )}
        </div>
      </section>
    </>
  );
}
