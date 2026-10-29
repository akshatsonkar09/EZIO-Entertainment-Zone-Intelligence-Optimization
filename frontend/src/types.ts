export type DomainType = 'movie' | 'anime' | 'book';
export type FilterDomainType = 'all' | DomainType;

export interface SearchResultItem {
  id: string;
  title: string;
  media_type: DomainType | string;
  score: number;
  release_year?: number | null;
  genres?: string | null;
  overview?: string | null;
  extra?: Record<string, any>;
}

export interface SearchResponse {
  user_query: string;
  domain?: string | null;
  total_results: number;
  results: SearchResultItem[];
}

export interface ItemDetail {
  id: string;
  media_type: DomainType | string;
  title: string;
  release_year?: number | null;
  overview?: string | null;
  genres: string[];
  metadata: Record<string, any>;
}

export interface MetadataCategories {
  domains: string[];
  genres: Record<string, string[]>;
  years: Record<string, { min: number | null; max: number | null }>;
}

export interface BrowseParams {
  domain?: DomainType;
  genre?: string;
  release_year_min?: number;
  release_year_max?: number;
  limit?: number;
}
