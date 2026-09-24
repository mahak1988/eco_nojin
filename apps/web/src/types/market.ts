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
  icon?: string;
  image?: string;
  parentId?: string;
  level: number;
  sortOrder: number;
  isActive: boolean;
  productCount: number;
  children?: Category[];
  provenance: ProvenanceStamp;
}

export interface CategoryTree {
  categories: Category[];
  totalCategories: number;
  maxDepth: number;
  provenance: ProvenanceStamp;
}

export interface ProductListing {
  id: string;
  slug: string;
  name: Record<string, string>;
  description?: Record<string, string>;
  shortDescription?: Record<string, string>;
  images: string[];
  thumbnail?: string;
  price: number;
  currency: string;
  unit: string;
  organic: boolean;
  certifications: string[];
  producer: {
    id: string;
    name: string;
    slug: string;
    rating: number;
  };
  category: {
    id: string;
    slug: string;
    name: Record<string, string>;
  };
  location: {
    latitude: number;
    longitude: number;
    address?: string;
  };
  carbonFootprint?: number;
  waterFootprint?: number;
  inStock: boolean;
  stockQuantity?: number;
  tags: string[];
  createdAt: string;
  updatedAt: string;
}

export interface ProductListResponse {
  products: ProductListing[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface SearchFilters {
  query?: string;
  category?: string;
  subcategory?: string;
  organic?: boolean;
  certifications?: string[];
  priceMin?: number;
  priceMax?: number;
  carbonFootprintMax?: number;
  waterFootprintMax?: number;
  latitude?: number;
  longitude?: number;
  radiusKm?: number;
  sortBy?: 'relevance' | 'price_asc' | 'price_desc' | 'newest' | 'popular' | 'rating';
  page?: number;
  pageSize?: number;
}

export interface SearchSuggestionsResponse {
  suggestions: string[];
  categories: string[];
  products: string[];
}

export interface SearchHistoryResponse {
  searches: Array<{
    query: string;
    timestamp: string;
    resultCount: number;
  }>;
}

export interface VisualSearchResponse {
  products: ProductListing[];
  similarImages: string[];
}

export interface AdvancedSearchRequest {
  filters: SearchFilters;
  semanticQuery?: string;
  visualSearchImage?: string;
  voiceQuery?: string;
}