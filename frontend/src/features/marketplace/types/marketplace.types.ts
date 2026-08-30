/**
 * Marketplace Types
 * ==================
 * Type definitions for Marketplace dashboard.
 *
 * @module features/marketplace/types
 */

// ─────────────────────────────────────────────────────────────────────
// Order Status
// ─────────────────────────────────────────────────────────────────────

/** All possible order statuses */
export type OrderStatus =
  | 'pending'
  | 'confirmed'
  | 'completed'
  | 'cancelled'
  | 'unknown';

// ─────────────────────────────────────────────────────────────────────
// Core Entities
// ─────────────────────────────────────────────────────────────────────

/** Marketplace product */
export interface Product {
  id: string;
  name: string;
  producer?: string;
  price: number;
  stock?: number;
  status?: string;
  category?: string;
}

/** Marketplace order */
export interface Order {
  id: string;
  total?: number;
  amount?: number;
  status: OrderStatus;
  customerName?: string;
  createdAt?: string;
  items?: OrderItem[];
}

/** Order item */
export interface OrderItem {
  productId: string;
  productName: string;
  quantity: number;
  price: number;
}

/** Marketplace statistics */
export interface MarketplaceStats {
  total_products?: number;
  total_orders?: number;
  total_revenue?: number;
  avg_order_value?: number;
  pending_orders?: number;
}

// ─────────────────────────────────────────────────────────────────────
// Derived Data
// ─────────────────────────────────────────────────────────────────────

/** Pie chart data point */
export interface PieDataPoint {
  name: string;
  value: number;
}

/** Derived data computed from orders (memoized) */
export interface DerivedOrderData {
  pendingOrders: Order[];
  completedOrders: Order[];
  totalRevenue: number;
  avgOrderValue: number;
  pieData: PieDataPoint[];
}
