import type { BrowseParams, ItemDetail, MetadataCategories, SearchResponse } from './types';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

export async function searchAPI(query: string, domain?: string | null, topK: number = 10): Promise<SearchResponse> {
  const cleanQuery = query.trim();
  if (!cleanQuery) {
    throw new Error('Search query cannot be empty.');
  }

  const payload: Record<string, any> = {
    query: cleanQuery,
    top_k: topK,
  };
  if (domain && domain !== 'all') {
    payload.domain = domain;
  }

  const res = await fetch(`${API_BASE}/api/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    let errorDetail = 'Search request failed';
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

export async function getItemAPI(itemId: string): Promise<ItemDetail> {
  const res = await fetch(`${API_BASE}/api/items/${encodeURIComponent(itemId)}`);
  if (!res.ok) {
    if (res.status === 404) {
      throw new Error(`Item "${itemId}" was not found in the catalog.`);
    }
    throw new Error('Failed to retrieve item metadata.');
  }
  return res.json();
}

export async function getRandomItemAPI(domain?: string | null): Promise<ItemDetail> {
  const param = domain && domain !== 'all' ? `?domain=${encodeURIComponent(domain)}` : '';
  const res = await fetch(`${API_BASE}/api/random${param}`);
  if (!res.ok) {
    throw new Error('Failed to discover random item.');
  }
  return res.json();
}

export async function getCategoriesAPI(): Promise<MetadataCategories> {
  const res = await fetch(`${API_BASE}/api/metadata/categories`);
  if (!res.ok) {
    throw new Error('Failed to fetch metadata categories.');
  }
  return res.json();
}

export async function browseMetadataAPI(params: BrowseParams): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE}/api/browse`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    throw new Error('Failed to browse metadata catalog.');
  }
  return res.json();
}
