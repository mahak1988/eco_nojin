/** Marketplace Context — provides cart, vendor, and user marketplace state. */

import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import { useToast } from '../components/ui/Toast';
import {
  addToCart as apiAddToCart,
  removeFromCart as apiRemoveFromCart,
  updateCartItemQuantity as apiUpdateCartItemQuantity,
  getCart,
  fetchOrders,
  fetchWishlist,
} from '../lib/marketplaceApi';
import type { Cart, CartItem, Order, Vendor, Product } from '../lib/marketplaceTypes';

interface MarketplaceContextValue {
  cart: Cart;
  cartLoading: boolean;
  selectedVendor: Vendor | null;
  orders: Order[];
  ordersLoading: boolean;
  wishlist: Product[];
  wishlistLoading: boolean;

  // Cart actions
  addToCart: (items: CartItem[]) => Promise<void>;
  removeFromCart: (productId: string) => Promise<void>;
  updateCartItemQuantity: (productId: string, quantity: number) => Promise<void>;
  refreshCart: () => Promise<void>;

  // Wishlist actions
  addToWishlist: (productId: string) => Promise<void>;
  removeFromWishlist: (productId: string) => Promise<void>;
  refreshWishlist: () => Promise<void>;
  isInWishlist: (productId: string) => boolean;

  // Vendor
  selectVendor: (vendor: Vendor | null) => void;

  // Orders
  refreshOrders: () => Promise<void>;
  addOrder: (order: Order) => void;
}

const MarketplaceContext = createContext<MarketplaceContextValue | null>(null);

const initialCart: Cart = { cart_id: null, items: [], total_items: 0, subtotal: 0 };

export function MarketplaceProvider({ children }: { children: ReactNode }) {
  const [cart, setCart] = useState<Cart>(initialCart);
  const [cartLoading, setCartLoading] = useState(false);
  const [selectedVendor, setSelectedVendor] = useState<Vendor | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [ordersLoading, setOrdersLoading] = useState(false);
  const [wishlist, setWishlist] = useState<Product[]>([]);
  const [wishlistLoading, setWishlistLoading] = useState(false);
  const { showToast } = useToast();

  const refreshCart = useCallback(async () => {
    setCartLoading(true);
    try {
      const data = await getCart();
      setCart(data);
    } catch (err: any) {
      showToast({ type: 'error', title: 'خطا در بارگذاری سبد', description: err.message });
    } finally {
      setCartLoading(false);
    }
  }, [showToast]);

  const addToCart = useCallback(async (items: CartItem[]) => {
    try {
      await apiAddToCart(items);
      await refreshCart();
      showToast({ type: 'success', title: 'به سبد اضافه شد' });
    } catch (err: any) {
      showToast({ type: 'error', title: 'خطا در اضافه کردن', description: err.message });
    }
  }, [refreshCart, showToast]);

  const removeFromCart = useCallback(async (productId: string) => {
    try {
      await apiRemoveFromCart(productId);
      await refreshCart();
      showToast({ type: 'success', title: 'از سبد حذف شد' });
    } catch (err: any) {
      showToast({ type: 'error', title: 'خطا در حذف', description: err.message });
    }
  }, [refreshCart, showToast]);

  const updateCartItemQuantity = useCallback(async (productId: string, quantity: number) => {
    try {
      await apiUpdateCartItemQuantity(productId, quantity);
      await refreshCart();
    } catch (err: any) {
      showToast({ type: 'error', title: 'خطا در به‌روزرسانی تعداد', description: err.message });
    }
  }, [refreshCart, showToast]);

  const refreshWishlist = useCallback(async () => {
    setWishlistLoading(true);
    try {
      const data = await fetchWishlist();
      setWishlist(data.items);
    } catch (err: any) {
      showToast({ type: 'error', title: 'خطا در بارگذاری علاقه‌مندی‌ها', description: err.message });
    } finally {
      setWishlistLoading(false);
    }
  }, [showToast]);

  const addToWishlist = useCallback(async (productId: string) => {
    try {
      await addToWishlist(productId);
      await refreshWishlist();
      showToast({ type: 'success', title: 'به علاقه‌مندی‌ها اضافه شد' });
    } catch (err: any) {
      showToast({ type: 'error', title: 'خطا در اضافه کردن', description: err.message });
    }
  }, [refreshWishlist, showToast]);

  const removeFromWishlist = useCallback(async (productId: string) => {
    try {
      await removeFromWishlist(productId);
      await refreshWishlist();
      showToast({ type: 'success', title: 'از علاقه‌مندی‌ها حذف شد' });
    } catch (err: any) {
      showToast({ type: 'error', title: 'خطا در حذف', description: err.message });
    }
  }, [refreshWishlist, showToast]);

  const isInWishlist = useCallback((productId: string) => {
    return wishlist.some((p) => p.id === productId);
  }, [wishlist]);

  const selectVendor = useCallback((vendor: Vendor | null) => {
    setSelectedVendor(vendor);
  }, []);

  const refreshOrders = useCallback(async () => {
    setOrdersLoading(true);
    try {
      const data = await fetchOrders();
      setOrders(data.orders);
    } catch (err: any) {
      showToast({ type: 'error', title: 'خطا در بارگذاری سفارشات', description: err.message });
    } finally {
      setOrdersLoading(false);
    }
  }, [showToast]);

  const addOrder = useCallback((order: Order) => {
    setOrders((prev) => [order, ...prev]);
  }, []);

  return (
    <MarketplaceContext.Provider
      value={{
        cart,
        cartLoading,
        selectedVendor,
        orders,
        ordersLoading,
        wishlist,
        wishlistLoading,
        addToCart,
        removeFromCart,
        updateCartItemQuantity,
        refreshCart,
        addToWishlist,
        removeFromWishlist,
        refreshWishlist,
        isInWishlist,
        selectVendor,
        refreshOrders,
        addOrder,
      }}
    >
      {children}
    </MarketplaceContext.Provider>
  );
}

export function useMarketplace(): MarketplaceContextValue {
  const value = useContext(MarketplaceContext);
  if (!value) {
    throw new Error('useMarketplace must be used within a MarketplaceProvider');
  }
  return value;
}
