/** Marketplace layout — dedicated navigation for marketplace section. */

import { useState, useEffect, useRef } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useBilingual } from '../hooks/useBilingual';
import { useMarketplace } from '../context/MarketplaceContext';
import { useAuth } from '../context/AuthContext';
import Seo from '../components/ui/Seo';
import { searchProducts } from '../lib/marketplaceApi';
import {
  Store,
  ShoppingCart,
  Search,
  User,
  Settings,
  Menu,
  X,
} from 'lucide-react';

const navItems = [
  { to: '/marketplace', labelFa: 'کاتالوگ', labelEn: 'Catalog', icon: Store },
  { to: '/marketplace/cart', labelFa: 'سبد خرید', labelEn: 'Cart', icon: ShoppingCart },
  { to: '/marketplace/apply', labelFa: 'فروشنده شوید', labelEn: 'Sell', icon: User },
];

export default function MarketplaceLayout({ children }: { children: React.ReactNode }) {
  const { lang } = useBilingual();
  const { cart } = useMarketplace();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [menuOpen, setMenuOpen] = useState(false);
  const [suggestions, setSuggestions] = useState<Array<{ id: string; name: string; price_per_kg: number }>>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [debounceTimer, setDebounceTimer] = useState<ReturnType<typeof setTimeout> | null>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  const isFa = lang === 'fa';
  const tMarket = (p: string, e: string) => (isFa ? p : e);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (search.trim()) {
      navigate(`/marketplace?q=${encodeURIComponent(search.trim())}`);
      setSearch('');
      setShowSuggestions(false);
    }
  };

  const handleSearchChange = (value: string) => {
    setSearch(value);
    if (debounceTimer) clearTimeout(debounceTimer);
    if (value.trim().length >= 2) {
      const timer = setTimeout(async () => {
        try {
          const result = await searchProducts(value.trim());
          setSuggestions(result.results.slice(0, 5));
          setShowSuggestions(true);
        } catch {
          setSuggestions([]);
          setShowSuggestions(false);
        }
      }, 300);
      setDebounceTimer(timer);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const handleSuggestionClick = (productId: string) => {
    navigate(`/marketplace/products/${productId}`);
    setSearch('');
    setShowSuggestions(false);
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const totalItems = cart.items.reduce((sum: number, item: { quantity?: number }) => sum + (item.quantity || 0), 0);

  return (
    <>
      <Seo
        title={tMarket('بازارگاه محلی اکو نوژین', 'Eco Nojin Local Marketplace')}
        description={tMarket('پیوند تولید کشاورز به بازار؛ با قیمت شفاف و عرضهٔ محلی.', 'Linking farmer production to the market — with transparent prices and local supply.')}
        path="/marketplace"
      />
      <div className="flex min-h-screen flex-col" dir={isFa ? 'rtl' : 'ltr'}>
        {/* Top bar */}
        <header className="sticky top-0 z-40 border-b border-white/10 bg-[var(--color-night-950)]/95 backdrop-blur">
          <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3 sm:px-6">
            {/* Logo */}
            <Link to="/marketplace" className="flex items-center gap-2 shrink-0">
              <div className="h-8 w-8 rounded-lg bg-[var(--color-leaf-500)] flex items-center justify-center">
                <Store className="h-5 w-5 text-night-950" aria-hidden />
              </div>
              <span className="font-display text-base font-bold text-[var(--color-night-100)] hidden sm:inline">
                {tMarket('بازارگاه', 'Market')}
              </span>
            </Link>

            {/* Search with Autocomplete */}
            <form onSubmit={handleSearch} className="flex-1 max-w-xl relative">
              <div className="relative">
                <Search className="absolute start-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-night-200)]/40" aria-hidden />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => handleSearchChange(e.target.value)}
                  onFocus={() => search.trim().length >= 2 && suggestions.length > 0 && setShowSuggestions(true)}
                  placeholder={tMarket('جستجوی محصول...', 'Search products...')}
                  className="w-full rounded-xl bg-white/5 border border-white/10 pl-9 pr-4 py-2 text-sm text-[var(--color-night-100)] outline-none placeholder:text-[var(--color-night-200)]/40 focus:border-[var(--color-leaf-400)]"
                  dir="ltr"
                  autoComplete="off"
                />
              </div>
              {showSuggestions && suggestions.length > 0 && (
                <div
                  ref={suggestionsRef}
                  className="absolute top-full left-0 right-0 mt-1 glass rounded-2xl border border-white/10 overflow-hidden shadow-lg z-50"
                >
                  {suggestions.map((product) => (
                    <button
                      key={product.id}
                      type="button"
                      onClick={() => handleSuggestionClick(product.id)}
                      className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-[var(--color-night-100)] hover:bg-white/5 transition-colors"
                    >
                      <span className="font-medium">{product.name}</span>
                      <span className="ml-auto text-[var(--color-leaf-400)] font-bold">{product.price_per_kg.toLocaleString()} IRR</span>
                    </button>
                  ))}
                </div>
              )}
            </form>

            {/* Actions */}
            <div className="flex items-center gap-1 sm:gap-2">
              <NavLink
                to="/marketplace/cart"
                className="relative rounded-xl p-2 text-[var(--color-night-200)]/70 hover:bg-white/5 hover:text-[var(--color-leaf-400)] transition"
                title={tMarket('سبد خرید', 'Cart')}
              >
                <ShoppingCart className="h-5 w-5" aria-hidden />
                {totalItems > 0 && (
                  <span className="absolute -top-0.5 -end-0.5 h-4 w-4 rounded-full bg-[var(--color-leaf-500)] text-[10px] font-bold text-night-950 flex items-center justify-center">
                    {totalItems}
                  </span>
                )}
              </NavLink>

              {user?.is_admin && (
                <NavLink
                  to="/marketplace/admin"
                  className="rounded-xl p-2 text-[var(--color-night-200)]/70 hover:bg-white/5 hover:text-yellow-400 transition"
                  title="Admin"
                >
                  <Settings className="h-5 w-5" aria-hidden />
                </NavLink>
              )}

              <button
                type="button"
                className="sm:hidden rounded-xl p-2 text-[var(--color-night-200)]/70 hover:bg-white/5"
                onClick={() => setMenuOpen(!menuOpen)}
              >
                {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
            </div>
          </div>

          {/* Navigation tabs */}
          <nav className="mx-auto hidden max-w-7xl gap-1 px-4 sm:flex sm:px-6">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `inline-flex items-center gap-1.5 rounded-t-lg px-3 py-2 text-sm font-bold transition ${
                    isActive
                      ? 'bg-[var(--color-leaf-500)]/10 text-[var(--color-leaf-400)] border-b-2 border-[var(--color-leaf-400)]'
                      : 'text-[var(--color-night-200)]/60 hover:text-[var(--color-night-100)]'
                  }`
                }
              >
                <item.icon className="h-4 w-4" aria-hidden />
                {isFa ? item.labelFa : item.labelEn}
              </NavLink>
            ))}
          </nav>

          {/* Mobile menu */}
          {menuOpen && (
            <div className="sm:hidden border-t border-white/10 px-4 py-2 space-y-1 bg-[var(--color-night-950)]">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={() => setMenuOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-bold ${
                      isActive ? 'bg-[var(--color-leaf-500)]/10 text-[var(--color-leaf-400)]' : 'text-[var(--color-night-200)]/60'
                    }`
                  }
                >
                  <item.icon className="h-4 w-4" aria-hidden />
                  {isFa ? item.labelFa : item.labelEn}
                </NavLink>
              ))}
            </div>
          )}
        </header>

        {/* Main content */}
        <main className="flex-1 pt-0" id="marketplace-content">
          {children}
        </main>

        {/* Footer brand bar */}
        <footer className="border-t border-white/10 bg-[var(--color-night-950)]/80 py-3 text-center text-xs text-[var(--color-night-200)]/40">
          Eco Nojin Marketplace — {tMarket('بازارگاه محلی کشاورزان', 'Local Farmers Marketplace')}
        </footer>
      </div>
    </>
  );
}
