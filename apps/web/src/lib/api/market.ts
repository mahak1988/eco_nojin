import { z } from 'zod';
import {
  type AdvancedSearchRequest,
  type Category,
  type CategoryTree,
  type ProductListing,
  type ProductListResponse,
  type SearchFilters,
  type SearchHistoryResponse,
  type SearchSuggestionsResponse,
  type VisualSearchResponse,
} from '@/types/market';
import { type ApiFailureKind, classifyApiFailure } from './cart';
import { apiGet, apiPost, createIdempotencyKey } from './client';

const PRODUCTS_BASE = '/api/v1/marketplace/products';
const SEARCH_BASE = `${PRODUCTS_BASE}/search`;

export const PRODUCTS_SOURCE = PRODUCTS_BASE;
export const SEARCH_SOURCE = SEARCH_BASE;

/**
 * The complete query contract of `GET /api/v1/marketplace/products`
 * (`services/api_gateway/routers/marketplace.py::list_products`). Any filter
 * outside this list has no server-side parameter, so the UI must report it as
 * unavailable instead of sending an invented key.
 */
export const PRODUCT_FILTER_PARAMS = [
  'category',
  'organic_only',
  'min_price',
  'max_price',
  'limit',
] as const;

export type ProductFilterParam = (typeof PRODUCT_FILTER_PARAMS)[number];

export type MarketResult<T> =
  | { ok: true; data: T; status: number }
  | { ok: false; error: string; status: number; kind: ApiFailureKind };

/**
 * Fields the gateway actually returns for a product. Everything the detail
 * endpoint does not send stays `undefined` so callers can render an unavailable
 * state instead of a fabricated value.
 */
export interface MarketProductDetail {
  id: string;
  name: string;
  category: string;
  description: string;
  pricePerKg: number;
  quantityAvailableKg: number;
  minimumOrderKg: number | null;
  organicCertified: boolean;
  carbonFootprintKgCo2: number | null;
  waterFootprintLiters: number | null;
  producerName: string;
  originLocation: string;
  harvestDate: string | null;
  batchNumber: string | null;
  traceabilityCode: string | null;
  images: string[];
}

export interface ProductSearchHit {
  id: string;
  name: string;
  pricePerKg: number;
}

/**
 * Payload of `GET /api/v1/marketplace/products/{id}/trace`
 * (`marketplace.py::get_product_trace`). The gateway sends `notes` per event and
 * a `qr_data` string; nothing else is part of the contract.
 */
export interface ProductTrace {
  product_id: string;
  traceability_code: string | null;
  events: Array<{
    timestamp: string;
    event: string;
    location: string;
    actor?: string | null;
    notes?: string | null;
  }>;
  qr_data?: string | null;
}

function failure<T>(error: string, status: number): MarketResult<T> {
  return { ok: false, error, status, kind: classifyApiFailure(status) };
}

function unavailable<T>(error: string): Promise<MarketResult<T>> {
  return Promise.resolve(failure<T>(error, 501));
}

function fromApi<T>(
  result: { ok: true; data: T; status: number } | { ok: false; error: string; status: number },
): MarketResult<T> {
  if (result.ok) return result;
  return failure<T>(result.error, result.status);
}

type BackendProduct = {
  id: string;
  name: string;
  slug?: string;
  category: string;
  description?: string;
  price_per_kg: number;
  quantity_available_kg: number;
  organic_certified: boolean;
  producer_name?: string;
  origin_location?: string;
  traceability_code?: string | null;
  images?: string[];
  minimum_order_kg?: number | null;
  carbon_footprint_kg_co2?: number | null;
  water_footprint_liters?: number | null;
  harvest_date?: string | null;
  batch_number?: string | null;
};

type BackendProductsResponse = { products: BackendProduct[]; count?: number };
type BackendSearchResponse = {
  query: string;
  results: Array<{ id: string; name: string; price_per_kg: number }>;
  count: number;
};

function mapProduct(product: BackendProduct): ProductListing {
  return {
    id: product.id,
    slug: product.slug || product.id,
    name: { en: product.name },
    description: product.description ? { en: product.description } : undefined,
    images: product.images ?? [],
    price: product.price_per_kg,
    unit: 'kg',
    organic: product.organic_certified,
    producer: { name: product.producer_name ?? '' },
    category: { id: product.category, slug: product.category, name: { en: product.category } },
    origin: product.origin_location,
    carbonFootprint: product.carbon_footprint_kg_co2 ?? undefined,
    waterFootprint: product.water_footprint_liters ?? undefined,
    inStock: product.quantity_available_kg > 0,
    stockQuantity: product.quantity_available_kg,
    traceabilityCode: product.traceability_code ?? undefined,
  };
}

function mapDetail(product: BackendProduct): MarketProductDetail {
  return {
    id: product.id,
    name: product.name,
    category: product.category,
    description: product.description ?? '',
    pricePerKg: product.price_per_kg,
    quantityAvailableKg: product.quantity_available_kg,
    minimumOrderKg: product.minimum_order_kg ?? null,
    organicCertified: product.organic_certified,
    carbonFootprintKgCo2: product.carbon_footprint_kg_co2 ?? null,
    waterFootprintLiters: product.water_footprint_liters ?? null,
    producerName: product.producer_name ?? '',
    originLocation: product.origin_location ?? '',
    harvestDate: product.harvest_date ?? null,
    batchNumber: product.batch_number ?? null,
    traceabilityCode: product.traceability_code ?? null,
    images: product.images ?? [],
  };
}

function productQuery(filters?: SearchFilters): string {
  const params = new URLSearchParams();
  if (filters?.category) params.set('category', filters.category);
  if (filters?.organic !== undefined) params.set('organic_only', String(filters.organic));
  if (filters?.priceMin !== undefined) params.set('min_price', String(filters.priceMin));
  if (filters?.priceMax !== undefined) params.set('max_price', String(filters.priceMax));
  params.set('limit', String(filters?.pageSize ?? 50));
  return params.toString();
}

export async function listProducts(
  filters?: SearchFilters,
): Promise<MarketResult<ProductListResponse>> {
  const result = await apiGet<BackendProductsResponse>(`${PRODUCTS_BASE}?${productQuery(filters)}`);
  if (!result.ok) return fromApi<ProductListResponse>(result);
  const products = result.data.products.map(mapProduct);
  return {
    ok: true,
    status: result.status,
    data: {
      products,
      total: result.data.count ?? products.length,
      page: 1,
      pageSize: products.length,
      totalPages: 1,
    },
  };
}

const optionalNumberField = z
  .string()
  .trim()
  .max(24)
  .transform((value) => (value === '' ? undefined : Number(value)))
  .refine((value) => value === undefined || Number.isFinite(value), {
    message: 'must be a number',
  })
  .refine((value) => value === undefined || (value as number) >= 0, {
    message: 'must not be negative',
  });

const optionalLimitField = optionalNumberField.refine(
  (value) => value === undefined || Number.isInteger(value),
  { message: 'must be a whole number' },
);

/**
 * Raw filter form state of the two connected product-search surfaces. It parses
 * to the exact `SearchFilters` subset `productQuery` turns into the five
 * supported query parameters, so no page can smuggle an unsupported filter into
 * the request.
 */
export const productFilterFormSchema = z
  .object({
    category: z.string().trim().max(120),
    organic: z.boolean(),
    priceMin: optionalNumberField,
    priceMax: optionalNumberField,
    limit: optionalLimitField,
  })
  .refine(
    (value) =>
      value.priceMin === undefined ||
      value.priceMax === undefined ||
      value.priceMin <= value.priceMax,
    { message: 'must not be below the minimum price', path: ['priceMax'] },
  )
  .refine((value) => value.limit === undefined || (value.limit as number) >= 1, {
    message: 'must be at least 1',
    path: ['limit'],
  });

export type ProductFilterForm = z.input<typeof productFilterFormSchema>;

export type ProductFilterParse =
  | { ok: true; filters: SearchFilters; applied: ProductFilterParam[] }
  | { ok: false; issues: string[] };

/**
 * Validates a filter form against the connected endpoint contract and reports
 * which of `PRODUCT_FILTER_PARAMS` will actually reach the gateway.
 */
export function parseProductFilterForm(input: ProductFilterForm): ProductFilterParse {
  const parsed = productFilterFormSchema.safeParse(input);
  if (!parsed.success) {
    return {
      ok: false,
      issues: parsed.error.issues.map(
        (issue) => `${issue.path.join('.') || 'filter'}: ${issue.message}`,
      ),
    };
  }

  const { category, organic, priceMin, priceMax, limit } = parsed.data;
  const filters: SearchFilters = { pageSize: (limit as number | undefined) ?? 50 };
  if (category) filters.category = category;
  if (organic) filters.organic = organic;
  if (priceMin !== undefined) filters.priceMin = priceMin;
  if (priceMax !== undefined) filters.priceMax = priceMax;

  // Reported in the endpoint's own parameter order so the UI lists exactly the
  // contract the gateway implements.
  const sent: Record<ProductFilterParam, boolean> = {
    category: Boolean(filters.category),
    organic_only: filters.organic === true,
    min_price: filters.priceMin !== undefined,
    max_price: filters.priceMax !== undefined,
    limit: true,
  };
  const applied = PRODUCT_FILTER_PARAMS.filter((param) => sent[param]);

  return { ok: true, filters, applied };
}

/** Real gateway path behind a product traceability view. */
export function productTraceSource(productId: string): string {
  return `${PRODUCTS_BASE}/${encodeURIComponent(productId)}/trace`;
}

/**
 * `/products/search` only returns id, name and unit price. The remaining
 * attributes are left out of the hit instead of being filled with placeholders.
 */
export async function searchProducts(query: string): Promise<MarketResult<ProductSearchHit[]>> {
  const params = new URLSearchParams({ q: query });
  const result = await apiGet<BackendSearchResponse>(`${SEARCH_BASE}?${params.toString()}`);
  if (!result.ok) return fromApi<ProductSearchHit[]>(result);
  return {
    ok: true,
    status: result.status,
    data: result.data.results.map((hit) => ({
      id: hit.id,
      name: hit.name,
      pricePerKg: hit.price_per_kg,
    })),
  };
}

export async function getProduct(productId: string): Promise<MarketResult<MarketProductDetail>> {
  const result = await apiGet<BackendProduct>(`${PRODUCTS_BASE}/${encodeURIComponent(productId)}`);
  if (!result.ok) return fromApi<MarketProductDetail>(result);
  return { ok: true, data: mapDetail(result.data), status: result.status };
}

export interface Bazaar {
  id: string;
  name: string;
  slug: string;
  description: string;
  marketplace_type: 'cooperative' | 'individual' | 'farmers_market' | 'mixed' | 'other';
  address: string;
  location: string;
  village_id: string;
  founder_ids: string[];
  status: string;
  admin_approved: boolean;
  marketing_enabled: boolean;
  branding_enabled: boolean;
  created_at: string;
}

export interface BazaarListResponse {
  marketplaces: Bazaar[];
}

export interface CreateBazaarInput {
  name: string;
  marketplaceType: Bazaar['marketplace_type'];
  description: string;
  address: string;
  location: string;
  villageId: string;
  acceptEcommerce: boolean;
  acceptTrading: boolean;
  rulesDocument: string;
  contactEmail: string;
  contactPhone: string;
}

export interface CreateBazaarResponse {
  marketplace_id: string;
  status: string;
}

export const BAZAARS_SOURCE = '/api/v1/marketplace/marketplaces';

export async function listBazaars(): Promise<MarketResult<Bazaar[]>> {
  const result = await apiGet<BazaarListResponse>(`${BAZAARS_SOURCE}?limit=100`);
  return fromApi<Bazaar[]>(
    result.ok ? { ok: true, data: result.data.marketplaces, status: result.status } : result,
  );
}

export async function getBazaar(id: string): Promise<MarketResult<Bazaar>> {
  const result = await apiGet<Bazaar>(`${BAZAARS_SOURCE}/${encodeURIComponent(id)}`);
  return fromApi<Bazaar>(result);
}

export async function createBazaar(
  input: CreateBazaarInput,
): Promise<MarketResult<CreateBazaarResponse>> {
  const result = await apiPost<CreateBazaarResponse>(
    BAZAARS_SOURCE,
    {
      name: input.name,
      marketplace_type: input.marketplaceType,
      description: input.description,
      address: input.address,
      location: input.location,
      village_id: input.villageId,
      founder_ids: [],
      e_commerce_rules_accepted: input.acceptEcommerce,
      buy_sell_rules_accepted: input.acceptTrading,
      rules_document: input.rulesDocument,
      contact_email: input.contactEmail,
      contact_phone: input.contactPhone,
    },
    { headers: { 'Idempotency-Key': createIdempotencyKey() } },
  );
  return fromApi(result);
}

export async function getProductTrace(productId: string): Promise<MarketResult<ProductTrace>> {
  const result = await apiGet<ProductTrace>(productTraceSource(productId));
  return fromApi<ProductTrace>(result);
}

/* Capabilities with no connected endpoint stay explicitly unavailable. */

const UNSEARCHABLE = 'Unconnected marketplace search capability';

export function getCategoryTree(): Promise<MarketResult<CategoryTree>> {
  return unavailable(UNSEARCHABLE);
}

export function getCategoryBySlug(_slug: string): Promise<MarketResult<Category>> {
  return unavailable(UNSEARCHABLE);
}

export function getCategoryChildren(_parentSlug: string): Promise<MarketResult<Category[]>> {
  return unavailable(UNSEARCHABLE);
}

export function getSearchSuggestions(
  _query: string,
  _limit?: number,
): Promise<MarketResult<SearchSuggestionsResponse>> {
  return unavailable(UNSEARCHABLE);
}

export function getSearchAutocomplete(
  _query: string,
  _limit?: number,
): Promise<MarketResult<string[]>> {
  return unavailable(UNSEARCHABLE);
}

export function getSearchHistory(): Promise<MarketResult<SearchHistoryResponse>> {
  return unavailable(UNSEARCHABLE);
}

export function visualSearch(_request: {
  image: string;
  filters?: SearchFilters;
}): Promise<MarketResult<VisualSearchResponse>> {
  return unavailable(UNSEARCHABLE);
}

export function semanticSearch(_request: {
  query: string;
  filters?: SearchFilters;
  useEmbeddings?: boolean;
}): Promise<MarketResult<ProductListResponse>> {
  return unavailable(UNSEARCHABLE);
}

export function advancedSearch(
  _request: AdvancedSearchRequest,
): Promise<MarketResult<ProductListResponse>> {
  return unavailable(UNSEARCHABLE);
}

export function searchByBarcode(_barcode: string): Promise<MarketResult<ProductListing | null>> {
  return unavailable(UNSEARCHABLE);
}

export function searchByNfc(_nfcTag: string): Promise<MarketResult<ProductListing | null>> {
  return unavailable(UNSEARCHABLE);
}

export function voiceSearch(
  _audioBlob: Blob,
  _filters?: SearchFilters,
): Promise<MarketResult<ProductListResponse>> {
  return unavailable(UNSEARCHABLE);
}
