/** Marketplace shared TypeScript types. */

export interface Marketplace {
  id: string;
  name: string;
  slug: string;
  description: string;
  marketplace_type: MarketplaceType;
  logo: string;
  banner: string;
  address: string;
  postal_code: string;
  location: string;
  village_id: string;
  founder_ids: string[];
  status: MarketplaceStatus;
  admin_approved: boolean;
  marketing_enabled: boolean;
  branding_enabled: boolean;
  created_at: string;
}

export interface MarketplaceMember {
  id: string;
  marketplace_id: string;
  user_id: string;
  role: MemberRole;
  joined_at: string;
  is_active: boolean;
}

export interface MarketplaceShop {
  id: string;
  marketplace_id: string;
  user_id: string;
  shop_name: string;
  shop_description: string;
  status: string;
  is_verified: boolean;
  created_at: string;
}

export type MarketplaceCategory =
  | 'grains'
  | 'fruits'
  | 'vegetables'
  | 'dairy'
  | 'meat'
  | 'spices'
  | 'handicraft'
  | 'village'
  | 'other';

export type MarketplaceType = 'rural' | 'tribal';
export type MarketplaceStatus = 'pending' | 'approved' | 'rejected' | 'inactive';
export type MemberRole = 'founder' | 'member' | 'admin';

export type ProductStatus = 'pending' | 'approved' | 'rejected' | 'out_of_stock';
export type VendorStatus = 'pending' | 'active' | 'suspended';
export type OrderStatus = 'pending' | 'confirmed' | 'paid' | 'shipped' | 'delivered' | 'cancelled';
export type PaymentStatus = 'pending' | 'paid' | 'refunded';
export type VendorRole = 'buyer' | 'seller' | 'admin';

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: VendorRole;
  is_admin: boolean;
  country: string | null;
}

export interface Product {
  id: string;
  name: string;
  slug: string;
  category: MarketplaceCategory;
  description: string;
  price: number;
  quantity_available: number;
  minimum_order: number;
  organic_certified: boolean;
  carbon_footprint_kg_co2: number;
  water_footprint_liters: number;
  producer_name: string;
  producer_id: string;
  origin_location: string;
  harvest_date: string | null;
  batch_number: string;
  traceability_code: string;
  pgs_certified: boolean;
  status: ProductStatus;
  images: string[];
  tags: string[];
  rating: number;
  review_count: number;
}

export interface Vendor {
  id: string;
  user_id: string;
  shop_name: string;
  slug: string;
  description: string;
  location: string;
  village_id: string;
  logo: string | null;
  banner: string | null;
  rating: number;
  total_sales: number;
  certifications: string[];
  is_verified: boolean;
  status: VendorStatus;
  created_at: string;
}

export interface CartItem {
  product_id: string;
  quantity: number;
}

export interface Cart {
  cart_id: string | null;
  items: CartItem[];
  total_items: number;
  subtotal: number;
}

export interface OrderItem {
  product_id: string;
  product_name: string;
  quantity_kg: number;
  unit_price: number;
}

export interface Order {
  id: string;
  order_number: string;
  buyer_id: string;
  seller_id: string;
  items: OrderItem[];
  subtotal: number;
  platform_fee: number;
  landscape_fee: number;
  total: number;
  shipping_address: Record<string, unknown>;
  status: OrderStatus;
  payment_status: PaymentStatus;
  tracking_code: string | null;
  created_at: string;
}

export interface TraceEvent {
  timestamp: string;
  event: string;
  location: string;
  actor: string;
  notes: string;
}

export interface ProductSearchParams {
  category?: MarketplaceCategory;
  organic_only?: boolean;
  min_price?: number;
  max_price?: number;
  q?: string;
  limit?: number;
  offset?: number;
  sort?: 'price_asc' | 'price_desc' | 'rating' | 'newest';
}

export interface MarketplaceApiResponse<T> {
  data: T;
  count?: number;
  offset?: number;
  limit?: number;
}
