/** Inventory shared TypeScript types. */

export interface SKU {
  id: number;
  sku_code: string;
  name: string;
  uom: string;
  category_id: number | null;
  standard_cost: string | null;
  warehouse_id: number | null;
  is_active: boolean;
  is_trackable: boolean;
}

export interface Warehouse {
  id: number;
  code: string;
  name: string;
  city: string | null;
  is_active: boolean;
}

export interface Location {
  id: number;
  warehouse_id: number;
  code: string;
  location_type: string;
}

export type MovementType =
  | 'receipt'
  | 'issue'
  | 'transfer'
  | 'adjust'
  | 'return'
  | 'scrap';

export interface Movement {
  id: number;
  movement_type: MovementType;
  sku_id: number;
  sku_code: string;
  warehouse_id: number;
  qty: string;
  unit_cost: string | null;
  total_cost: string | null;
  reference_type: string | null;
  reference_id: string | null;
  reference_number: string | null;
  created_by: string | null;
  approved_by: string | null;
  approved_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface Balance {
  sku_code: string;
  warehouse_id: number | null;
  location_id: number | null;
  on_hand: string;
  reserved: string;
  blocked: string;
  in_transit: string;
  available: string;
}

export type ReservationStatus = 'active' | 'consumed' | 'released' | 'expired';

export interface Reservation {
  id: number;
  sku_id: number;
  sku_code: string;
  warehouse_id: number;
  location_id: number | null;
  lot_id: number | null;
  qty: string;
  status: ReservationStatus;
  reference_type: string;
  reference_id: string;
  reference_line_id: string | null;
  expires_at: string | null;
  consumed_qty: string;
  created_by: string;
  created_at: string;
  released_at: string | null;
  consumed_at: string | null;
}

export interface Stocktake {
  id: number;
  stocktake_number: string;
  warehouse_id: number;
  warehouse_name: string | null;
  status: 'planned' | 'in_progress' | 'completed' | 'cancelled' | 'variance_review';
  stocktake_type: string;
  planned_start: string | null;
  planned_end: string | null;
  actual_start: string | null;
  actual_end: string | null;
  counted_by: string | null;
  reviewed_by: string | null;
  notes: string | null;
  created_by: string;
  created_at: string;
  updated_at: string | null;
}

export interface SKUPagination {
  skus: SKU[];
  count: number;
}

export interface WarehousePagination {
  warehouses: Warehouse[];
  count: number;
}

export interface MovementPagination {
  movements: Movement[];
  count: number;
}
