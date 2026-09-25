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
import { apiGet } from './client';

const PRODUCTS_BASE = '/api/v1/marketplace/products';
const SEARCH_BASE = '/api/v1/marketplace/products/search';

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
  traceability_code?: string;
  images?: string[];
  carbon_footprint_kg_co2?: number;
  water_footprint_liters?: number;
};

type BackendProductsResponse = { products: BackendProduct[]; count?: number };
type BackendSearchResponse = {
  query: string;
  results: Array<Pick<BackendProduct, 'id' | 'name' | 'price_per_kg'>>;
  count: number;
};

type Result<T> = { ok: true; data: T } | { ok: false; error: string };

function unavailable<T>(): Promise<Result<T>> {
  return Promise.resolve({ ok: false, error: 'This marketplace capability is unavailable' });
}

function mapProduct(product: BackendProduct): ProductListing {
  return {
    id: product.id,
    slug: product.slug ?? product.id,
    name: { en: product.name },
    description: product.description ? { en: product.description } : undefined,
    images: product.images ?? [],
    price: product.price_per_kg,
    unit: 'kg',
    organic: product.organic_certified,
    producer: {
      name: product.producer_name ?? '',
    },
    category: {
      id: product.category,
      slug: product.category,
      name: { en: product.category },
    },
    origin: product.origin_location,
    carbonFootprint: product.carbon_footprint_kg_co2,
    waterFootprint: product.water_footprint_liters,
    inStock: product.quantity_available_kg > 0,
    stockQuantity: product.quantity_available_kg,
    traceabilityCode: product.traceability_code,
  };
}

function mapProducts(products: BackendProduct[]): ProductListResponse {
  return {
    products: products.map(mapProduct),
    total: products.length,
    page: 1,
    pageSize: products.length,
    totalPages: 1,
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

export function getCategoryTree(): Promise<Result<CategoryTree>> {
  return unavailable();
}

export function getCategoryBySlug(_slug: string): Promise<Result<Category>> {
  return unavailable();
}

export function getCategoryChildren(_parentSlug: string): Promise<Result<Category[]>> {
  return unavailable();
}

export async function getProductsByCategory(
  categorySlug: string,
  filters?: SearchFilters,
): Promise<Result<ProductListResponse>> {
  const result = await apiGet<BackendProductsResponse>(
    `${PRODUCTS_BASE}?${productQuery({ ...filters, category: categorySlug })}`,
  );
  if (!result.ok) return result;
  return { ok: true, data: mapProducts(result.data.products) };
}

export async function searchProducts(filters: SearchFilters): Promise<Result<ProductListResponse>> {
  if (filters.query) {
    const params = new URLSearchParams({ q: filters.query });
    const result = await apiGet<BackendSearchResponse>(`${SEARCH_BASE}?${params.toString()}`);
    if (!result.ok) return result;
    return {
      ok: true,
      data: mapProducts(
        result.data.results.map((item) => ({
          ...item,
          category: '',
          quantity_available_kg: 0,
          organic_certified: false,
        })),
      ),
    };
  }
  const result = await apiGet<BackendProductsResponse>(`${PRODUCTS_BASE}?${productQuery(filters)}`);
  if (!result.ok) return result;
  return { ok: true, data: mapProducts(result.data.products) };
}

export function getSearchSuggestions(
  _query: string,
  _limit?: number,
): Promise<Result<SearchSuggestionsResponse>> {
  return unavailable();
}

export function getSearchAutocomplete(_query: string, _limit?: number): Promise<Result<string[]>> {
  return unavailable();
}

export function getSearchHistory(): Promise<Result<SearchHistoryResponse>> {
  return unavailable();
}

export function visualSearch(_request: {
  image: string;
  filters?: SearchFilters;
}): Promise<Result<VisualSearchResponse>> {
  return unavailable();
}

export function semanticSearch(_request: {
  query: string;
  filters?: SearchFilters;
  useEmbeddings?: boolean;
}): Promise<Result<ProductListResponse>> {
  return unavailable();
}

export function advancedSearch(
  _request: AdvancedSearchRequest,
): Promise<Result<ProductListResponse>> {
  return unavailable();
}

export function searchByBarcode(_barcode: string): Promise<Result<ProductListing | null>> {
  return unavailable();
}

export async function getProduct(productId: string): Promise<Result<ProductListing | null>> {
  const result = await apiGet<BackendProduct>(`${PRODUCTS_BASE}/${encodeURIComponent(productId)}`);
  if (!result.ok) return result;
  return { ok: true, data: mapProduct(result.data) };
}

export async function getProductTrace(productId: string): Promise<Result<unknown>> {
  return apiGet<unknown>(`${PRODUCTS_BASE}/${encodeURIComponent(productId)}/trace`);
}

export function searchByNfc(_nfcTag: string): Promise<Result<ProductListing | null>> {
  return unavailable();
}

export function voiceSearch(
  _audioBlob: Blob,
  _filters?: SearchFilters,
): Promise<
  | { ok: true; data: ProductListResponse; status: number }
  | { ok: false; error: string; status: number }
> {
  return Promise.resolve({ ok: false, error: 'Voice search is unavailable', status: 501 });
}
