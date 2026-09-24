import { z } from 'zod';

export interface ProvenanceStamp {
  source: string;
  verified?: boolean;
  timestamp?: string;
  method?: string;
}

export interface Category {
  id: string;
  slug: string;
  name: string;
  description?: string;
  level: 1 | 2 | 3;
  parentId?: string;
  children?: Category[];
  productCount: number;
  icon?: string;
  image?: string;
  provenance: ProvenanceStamp;
}

export interface CategoryTree {
  categories: Category[];
  totalCount: number;
  provenance: ProvenanceStamp;
}

export interface ProductListing {
  id: string;
  slug: string;
  name: string;
  description: string;
  categoryId: string;
  categoryPath: string[];
  pricePerKg: number;
  quantityAvailableKg: number;
  minimumOrderKg: number;
  organicCertified: boolean;
  certifications: string[];
  carbonFootprintKgCo2: number;
  waterFootprintLiters: number;
  producerId: string;
  producerName: string;
  originLocation: string;
  harvestDate?: string;
  batchNumber?: string;
  traceabilityCode: string;
  images: string[];
  provenance: ProvenanceStamp;
  createdAt: string;
  updatedAt: string;
}

export interface ProductListResponse {
  products: ProductListing[];
  totalCount: number;
  page: number;
  pageSize: number;
  filters: SearchFilters;
  provenance: ProvenanceStamp;
}

export interface SearchFilters {
  query?: string;
  categoryId?: string;
  categorySlug?: string;
  level1Slug?: string;
  level2Slug?: string;
  level3Slug?: string;
  organicOnly?: boolean;
  certifications?: string[];
  minPrice?: number;
  maxPrice?: number;
  minCarbonFootprint?: number;
  maxCarbonFootprint?: number;
  minWaterFootprint?: number;
  maxWaterFootprint?: number;
  producerId?: string;
  location?: string;
  radiusKm?: number;
  sortBy?: 'relevance' | 'price_asc' | 'price_desc' | 'newest' | 'popular' | 'rating';
  sortOrder?: 'asc' | 'desc';
  page?: number;
  pageSize?: number;
}

export interface SearchSuggestionsResponse {
  suggestions: string[];
  categories: { slug: string; name: string; count: number }[];
  products: { id: string; name: string; category: string }[];
  provenance: ProvenanceStamp;
}

export interface SearchHistoryItem {
  id: string;
  query: string;
  filters: SearchFilters;
  resultCount: number;
  timestamp: string;
}

export interface SearchHistoryResponse {
  history: SearchHistoryItem[];
  provenance: ProvenanceStamp;
}

export interface VisualSearchRequest {
  image: string;
  filters?: SearchFilters;
}

export interface VisualSearchResult {
  productId: string;
  name: string;
  similarity: number;
  category: string;
  pricePerKg: number;
  images: string[];
}

export interface VisualSearchResponse {
  results: VisualSearchResult[];
  queryImage: string;
  provenance: ProvenanceStamp;
}

export interface SemanticSearchRequest {
  query: string;
  filters?: SearchFilters;
  useEmbeddings?: boolean;
}

export interface AdvancedSearchRequest extends SearchFilters {
  semanticQuery?: string;
  visualSearch?: VisualSearchRequest;
  voiceQuery?: string;
  barcode?: string;
  nfcTag?: string;
}

export const CategorySchema = z.object({
  id: z.string(),
  slug: z.string(),
  name: z.string(),
  description: z.string().optional(),
  level: z.number().int().min(1).max(3),
  parentId: z.string().optional(),
  children: z.lazy(() => z.array(CategorySchema)).optional(),
  productCount: z.number().int(),
  icon: z.string().optional(),
  image: z.string().optional(),
  provenance: z.object({
    source: z.string(),
    verified: z.boolean().optional(),
    timestamp: z.string().optional(),
    method: z.string().optional(),
  }),
});

export const CategoryTreeSchema = z.object({
  categories: z.array(CategorySchema),
  totalCount: z.number().int(),
  provenance: z.object({
    source: z.string(),
    verified: z.boolean().optional(),
    timestamp: z.string().optional(),
    method: z.string().optional(),
  }),
});

export const ProductListingSchema = z.object({
  id: z.string(),
  slug: z.string(),
  name: z.string(),
  description: z.string(),
  categoryId: z.string(),
  categoryPath: z.array(z.string()),
  pricePerKg: z.number(),
  quantityAvailableKg: z.number(),
  minimumOrderKg: z.number(),
  organicCertified: z.boolean(),
  certifications: z.array(z.string()),
  carbonFootprintKgCo2: z.number(),
  waterFootprintLiters: z.number(),
  producerId: z.string(),
  producerName: z.string(),
  originLocation: z.string(),
  harvestDate: z.string().optional(),
  batchNumber: z.string().optional(),
  traceabilityCode: z.string(),
  images: z.array(z.string()),
  provenance: z.object({
    source: z.string(),
    verified: z.boolean().optional(),
    timestamp: z.string().optional(),
    method: z.string().optional(),
  }),
  createdAt: z.string(),
  updatedAt: z.string(),
});

export const SearchFiltersSchema = z.object({
  query: z.string().optional(),
  categoryId: z.string().optional(),
  categorySlug: z.string().optional(),
  level1Slug: z.string().optional(),
  level2Slug: z.string().optional(),
  level3Slug: z.string().optional(),
  organicOnly: z.boolean().optional(),
  certifications: z.array(z.string()).optional(),
  minPrice: z.number().optional(),
  maxPrice: z.number().optional(),
  minCarbonFootprint: z.number().optional(),
  maxCarbonFootprint: z.number().optional(),
  minWaterFootprint: z.number().optional(),
  maxWaterFootprint: z.number().optional(),
  producerId: z.string().optional(),
  location: z.string().optional(),
  radiusKm: z.number().optional(),
  sortBy: z.enum(['relevance', 'price_asc', 'price_desc', 'newest', 'popular', 'rating']).optional(),
  sortOrder: z.enum(['asc', 'desc']).optional(),
  page: z.number().int().optional(),
  pageSize: z.number().int().optional(),
});

export const ProvenanceStampSchema = z.object({
  source: z.string(),
  verified: z.boolean().optional(),
  timestamp: z.string().optional(),
  method: z.string().optional(),
});

export type {
  ProvenanceStamp,
  Category,
  CategoryTree,
  ProductListing,
  ProductListResponse,
  SearchFilters,
  SearchSuggestionsResponse,
  SearchHistoryItem,
  SearchHistoryResponse,
  VisualSearchRequest,
  VisualSearchResult,
  VisualSearchResponse,
  SemanticSearchRequest,
  AdvancedSearchRequest,
};