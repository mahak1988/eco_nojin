/** Marketplace API client — follows existing hydromaApi.ts patterns. */

import { getApiBase } from './api';
import type {
  Product,
  ProductSearchParams,
  Vendor,
  Cart,
  Order,
  CartItem,
  Marketplace,
  MarketplaceShop,
} from './marketplaceTypes';

const apiBase = getApiBase();

async function marketFetch<T>(
  path: string,
  options?: RequestInit & { skipAuth?: boolean },
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> | undefined),
  };
  const token = localStorage.getItem('hydrom…oken');
  if (token && !options?.skipAuth) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${apiBase}${path}`, {
    ...options,
    headers,
  });
  if (!res.ok) {
    throw new Error(`marketplace_error_${res.status}`);
  }
  return res.json() as T;
}

// --- Product queries ---

export async function fetchProducts(params?: ProductSearchParams): Promise<{ products: Product[]; count: number }> {
  const searchParams = new URLSearchParams();
  if (params?.category) searchParams.set('category', params.category);
  if (params?.organic_only) searchParams.set('organic_only', 'true');
  if (params?.min_price != null) searchParams.set('min_price', String(params.min_price));
  if (params?.max_price != null) searchParams.set('max_price', String(params.max_price));
  if (params?.q) searchParams.set('q', params.q);
  if (params?.limit) searchParams.set('limit', String(params.limit));
  if (params?.offset) searchParams.set('offset', String(params.offset));
  if (params?.sort) searchParams.set('sort', params.sort);

  const qs = searchParams.toString();
  return marketFetch<{ products: Product[]; count: number }>(
    `/api/v1/marketplace/products${qs ? `?${qs}` : ''}`,
  );
}

export async function fetchProduct(id: string): Promise<Product> {
  return marketFetch<Product>(`/api/v1/marketplace/products/${id}`);
}

export async function searchProducts(q: string): Promise<{ results: Array<{ id: string; name: string; price_per_kg: number }>; count: number }> {
  return marketFetch(`/api/v1/marketplace/products/search?q=${encodeURIComponent(q)}`);
}

export async function fetchProductTrace(productId: string): Promise<{ events: Array<{ timestamp: string; event: string; location: string; actor: string; notes: string }>; qr_data: Record<string, unknown> }> {
  return marketFetch(`/api/v1/marketplace/products/${productId}/trace`);
}

export async function uploadProductImages(productId: string, files: File[]): Promise<{ product_id: string; images: string[] }> {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  const token = localStorage.getItem('hydrom…oken');
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${apiBase}/api/v1/marketplace/products/${productId}/images`, {
    method: 'POST',
    headers,
    body: formData,
  });
  if (!res.ok) {
    throw new Error(`marketplace_error_${res.status}`);
  }
  return res.json() as Promise<{ product_id: string; images: string[] }>;
}

export async function fetchCategories(): Promise<Array<{ value: string; label: Record<string, string> }>> {
  return marketFetch('/api/v1/marketplace/categories');
}

export async function fetchProducers(): Promise<{ producers: Vendor[]; count: number }> {
  return marketFetch('/api/v1/marketplace/producers');
}

// --- Vendor queries ---

export async function fetchVendor(id: string): Promise<Vendor> {
  return marketFetch<Vendor>(`/api/v1/marketplace/vendors/${id}`);
}

export async function fetchVendorProducts(vendorId: string, limit = 20): Promise<{ products: Product[]; vendor_id: string }> {
  return marketFetch<{ products: Product[]; vendor_id: string }>(
    `/api/v1/marketplace/vendors/${vendorId}/products?limit=${limit}`,
  );
}

export async function fetchVendorOrders(vendorId: string, status?: string): Promise<{ orders: Order[]; count: number }> {
  const qs = status ? `?status=${encodeURIComponent(status)}` : '';
  return marketFetch<{ orders: Order[]; count: number }>(
    `/api/v1/marketplace/vendors/${vendorId}/orders${qs}`,
  );
}

export async function applyVendor(data: {
  shop_name: string;
  description: string;
  location: string;
  village_id: string;
  product_types: string;
  certifications: string;
  production_capacity: string;
  years_experience: string;
  contact_phone: string;
  social_media: string;
  operating_hours: string;
  delivery_area: string;
  currency: string;
  marketplace_id: string;
}): Promise<{ vendor_id: string; status: string }> {
  return marketFetch('/api/v1/marketplace/vendors', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// --- Cart mutations ---

export async function addToCart(items: CartItem[]): Promise<{ cart_id: string | null; items: CartItem[]; total_items: number }> {
  return marketFetch('/api/v1/marketplace/cart', {
    method: 'POST',
    body: JSON.stringify({ items }),
  });
}

export async function getCart(): Promise<Cart> {
  return marketFetch<Cart>('/api/v1/marketplace/cart');
}

export async function removeFromCart(productId: string): Promise<{ removed: string }> {
  return marketFetch<{ removed: string }>(`/api/v1/marketplace/cart/${productId}`, {
    method: 'DELETE',
  });
}

export async function updateCartItemQuantity(productId: string, quantity: number): Promise<{ cart_id: string | null; items: CartItem[]; total_items: number }> {
  return marketFetch<{ cart_id: string | null; items: CartItem[]; total_items: number }>(
    `/api/v1/marketplace/cart/${productId}`,
    {
      method: 'PATCH',
      body: JSON.stringify({ quantity }),
    }
  );
}

// --- Order mutations ---

export async function createOrder(data: { shipping_address: Record<string, unknown>; payment_method?: string }): Promise<Order> {
  return marketFetch<Order>('/api/v1/marketplace/orders', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function fetchOrders(status?: string): Promise<{ orders: Order[]; count: number }> {
  const qs = status ? `?status=${encodeURIComponent(status)}` : '';
  return marketFetch<{ orders: Order[]; count: number }>(`/api/v1/marketplace/orders${qs}`);
}

export async function fetchOrder(id: string): Promise<Order> {
  return marketFetch<Order>(`/api/v1/marketplace/orders/${id}`);
}

export async function fetchOrderTracking(orderId: string): Promise<{
  order_id: string;
  order_number: string;
  current_status: string;
  timeline: Array<{
    timestamp: string;
    status: string;
    title: string;
    description: string;
  }>;
}> {
  return marketFetch(`/api/v1/marketplace/orders/${orderId}/track`);
}

// --- Marketplace ---

export async function createMarketplace(data: {
  name: string;
  marketplace_type: string;
  description?: string;
  address?: string;
  postal_code?: string;
  location?: string;
  village_id: string;
  founder_ids?: string[];
  e_commerce_rules_accepted: boolean;
  buy_sell_rules_accepted: boolean;
  rules_document?: string;
  contact_email?: string;
  contact_phone?: string;
}): Promise<{ marketplace_id: string; status: string }> {
  return marketFetch('/api/v1/marketplace/marketplaces', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function fetchMarketplaces(params?: {
  marketplace_type?: string;
  village_id?: string;
  status?: string;
  limit?: number;
}): Promise<{ marketplaces: Marketplace[] }> {
  const searchParams = new URLSearchParams();
  if (params?.marketplace_type) searchParams.set('marketplace_type', params.marketplace_type);
  if (params?.village_id) searchParams.set('village_id', params.village_id);
  if (params?.status) searchParams.set('status', params.status);
  if (params?.limit) searchParams.set('limit', String(params.limit));
  const qs = searchParams.toString();
  return marketFetch<{ marketplaces: Marketplace[] }>(
    `/api/v1/marketplace/marketplaces${qs ? `?${qs}` : ''}`,
  );
}

export async function fetchMarketplace(marketplaceId: string): Promise<Marketplace> {
  return marketFetch<Marketplace>(`/api/v1/marketplace/marketplaces/${marketplaceId}`);
}

export async function fetchMarketplaceShops(marketplaceId: string, limit = 50): Promise<{ shops: MarketplaceShop[] }> {
  return marketFetch<{ shops: MarketplaceShop[] }>(
    `/api/v1/marketplace/marketplaces/${marketplaceId}/shops?limit=${limit}`,
  );
}

export async function approveMarketplace(marketplaceId: string, approve: boolean): Promise<{ marketplace_id: string; approved: boolean; status: string }> {
  return marketFetch(`/api/v1/marketplace/marketplaces/${marketplaceId}/approve?approve=${approve}`, {
    method: 'POST',
  });
}

export async function addMarketplaceMember(marketplaceId: string, userId: string, role: string = 'member'): Promise<{ member_id: string; status: string }> {
  return marketFetch(`/api/v1/marketplace/marketplaces/${marketplaceId}/members`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, role }),
  });
}

export async function createMarketplaceShop(marketplaceId: string, data: Record<string, unknown>): Promise<{ shop_id: string; status: string }> {
  return marketFetch(`/api/v1/marketplace/marketplaces/${marketplaceId}/shops`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// --- Admin ---

export async function adminApproveProduct(productId: string, approve: boolean): Promise<{ product_id: string; approved: boolean }> {
  return marketFetch(`/api/v1/marketplace/admin/products/${productId}/approve?approve=${approve}`, {
    method: 'PATCH',
  });
}

export async function adminApproveVendor(vendorId: string, approve: boolean): Promise<{ vendor_id: string; approved: boolean }> {
  return marketFetch(`/api/v1/marketplace/admin/vendors/${vendorId}/approve?approve=${approve}`, {
    method: 'PATCH',
  });
}

export async function adminStats(): Promise<{ total_products: number; total_producers: number; organic_products: number; orders: Record<string, unknown> }> {
  return marketFetch('/api/v1/marketplace/admin/stats');
}

// --- Wishlist ---

export async function fetchWishlist(): Promise<{ items: Product[]; count: number }> {
  return marketFetch('/api/v1/marketplace/wishlist');
}

export async function addToWishlist(productId: string): Promise<{ product_id: string; added: boolean }> {
  return marketFetch('/api/v1/marketplace/wishlist', {
    method: 'POST',
    body: JSON.stringify({ product_id: productId }),
  });
}

export async function removeFromWishlist(productId: string): Promise<{ product_id: string; removed: boolean }> {
  return marketFetch(`/api/v1/marketplace/wishlist/${productId}`, {
    method: 'DELETE',
  });
}
