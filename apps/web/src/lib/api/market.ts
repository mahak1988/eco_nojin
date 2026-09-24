import {
  type Category,
  type CategoryTree,
  type ProductListing,
  type ProductListResponse,
  type SearchFilters,
  type SearchSuggestionsResponse,
  type SearchHistoryResponse,
  type VisualSearchResponse,
  type AdvancedSearchRequest,
} from '@/types/market';
import { apiGet, apiPost } from './client';

const CATEGORIES_BASE = '/api/v1/market/categories';
const SEARCH_BASE = '/api/v1/market/search';

export async function getCategoryTree(): Promise<{ ok: true; data: CategoryTree } | { ok: false; error: string }> {
  return apiGet<CategoryTree>(`${CATEGORIES_BASE}/tree`);
}

export async function getCategoryBySlug(slug: string): Promise<{ ok: true; data: Category } | { ok: false; error: string }> {
  return apiGet<Category>(`${CATEGORIES_BASE}/${slug}`);
}

export async function getCategoryChildren(parentSlug: string): Promise<{ ok: true; data: Category[] } | { ok: false; error: string }> {
  return apiGet<Category[]>(`${CATEGORIES_BASE}/${parentSlug}/children`);
}

export async function getProductsByCategory(
  categorySlug: string,
  filters?: SearchFilters
): Promise<{ ok: true; data: ProductListResponse } | { ok: false; error: string }> {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        if (Array.isArray(value)) {
          value.forEach(v => params.append(key, String(v)));
        } else {
          params.set(key, String(value));
        }
      }
    });
  }
  const queryString = params.toString();
  return apiGet<ProductListResponse>(`${CATEGORIES_BASE}/${categorySlug}/products${queryString ? `?${queryString}` : ''}`);
}

export async function searchProducts(
  filters: SearchFilters
): Promise<{ ok: true; data: ProductListResponse } | { ok: false; error: string }> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value)) {
        value.forEach(v => params.append(key, String(v)));
      } else {
        params.set(key, String(value));
      }
    }
  });
  return apiGet<ProductListResponse>(`${SEARCH_BASE}?${params.toString()}`);
}

export async function getSearchSuggestions(
  query: string,
  limit?: number
): Promise<{ ok: true; data: SearchSuggestionsResponse } | { ok: false; error: string }> {
  const params = new URLSearchParams({ q: query });
  if (limit) params.set('limit', String(limit));
  return apiGet<SearchSuggestionsResponse>(`${SEARCH_BASE}/suggestions?${params.toString()}`);
}

export async function getSearchAutocomplete(
  query: string,
  limit?: number
): Promise<{ ok: true; data: string[] } | { ok: false; error: string }> {
  const params = new URLSearchParams({ q: query });
  if (limit) params.set('limit', String(limit));
  return apiGet<string[]>(`${SEARCH_BASE}/autocomplete?${params.toString()}`);
}

export async function getSearchHistory(): Promise<{ ok: true; data: SearchHistoryResponse } | { ok: false; error: string }> {
  return apiGet<SearchHistoryResponse>(`${SEARCH_BASE}/history`);
}

export async function visualSearch(
  request: { image: string; filters?: SearchFilters }
): Promise<{ ok: true; data: VisualSearchResponse } | { ok: false; error: string }> {
  return apiPost<VisualSearchResponse>(`${SEARCH_BASE}/visual`, request);
}

export async function semanticSearch(
  request: { query: string; filters?: SearchFilters; useEmbeddings?: boolean }
): Promise<{ ok: true; data: ProductListResponse } | { ok: false; error: string }> {
  return apiPost<ProductListResponse>(`${SEARCH_BASE}/semantic`, request);
}

export async function advancedSearch(
  request: AdvancedSearchRequest
): Promise<{ ok: true; data: ProductListResponse } | { ok: false; error: string }> {
  return apiPost<ProductListResponse>(`${SEARCH_BASE}/advanced`, request);
}

export async function searchByBarcode(
  barcode: string
): Promise<{ ok: true; data: ProductListing | null } | { ok: false; error: string }> {
  return apiGet<ProductListing | null>(`${SEARCH_BASE}/barcode/${encodeURIComponent(barcode)}`);
}

export async function searchByNfc(
  nfcTag: string
): Promise<{ ok: true; data: ProductListing | null } | { ok: false; error: string }> {
  return apiGet<ProductListing | null>(`${SEARCH_BASE}/nfc/${encodeURIComponent(nfcTag)}`);
}

export async function voiceSearch(
  audioBlob: Blob,
  filters?: SearchFilters
): Promise<{ ok: true; data: ProductListResponse; status: number } | { ok: false; error: string; status: number }> {
  const formData = new FormData();
  formData.append('audio', audioBlob);
  if (filters) {
    formData.append('filters', JSON.stringify(filters));
  }
  const API_BASE = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000';
  try {
    const res = await fetch(`${API_BASE}${SEARCH_BASE}/voice`, {
      method: 'POST',
      cache: 'no-store',
      body: formData,
    });
    const text = await res.text();
    let parsed: unknown;
    try {
      parsed = text ? JSON.parse(text) : undefined;
    } catch {
      parsed = text;
    }
    if (!res.ok) {
      const detail = typeof parsed === 'string' ? parsed.slice(0, 300) : ((parsed as Record<string, unknown> | undefined)?.detail as string) ?? res.statusText;
      return { ok: false, error: String(detail ?? 'request failed'), status: res.status };
    }
    return { ok: true, data: parsed as ProductListResponse, status: res.status };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err), status: 0 };
  }
}