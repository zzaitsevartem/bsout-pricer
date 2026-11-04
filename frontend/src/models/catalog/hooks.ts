import { useQuery } from '@tanstack/react-query';
import { catalogApi } from './service';
import type { CatalogSearchParams, CatalogSuggestionParams } from './schema';

export function useCatalogDevices(params: { q: string; limit?: number }, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['catalog', 'devices', params],
    queryFn: ({ signal }) => catalogApi.devices(params, signal).then((response) => response.data),
    enabled: (options?.enabled ?? true) && params.q.trim().length >= 2,
    staleTime: 60_000,
    retry: false,
  });
}

export function useCatalogFacets(params: CatalogSearchParams) {
  return useQuery({
    queryKey: ['catalog', 'facets', params],
    queryFn: () => catalogApi.facets(params).then((response) => response.data),
  });
}

export function useCatalogSearch(params: CatalogSearchParams) {
  return useQuery({
    queryKey: ['catalog', 'search', params],
    queryFn: () => catalogApi.search(params).then((r) => r.data),
  });
}

export function useCatalogProduct(productId: number) {
  return useQuery({
    queryKey: ['catalog', productId],
    queryFn: () => catalogApi.getById(productId).then((r) => r.data),
    enabled: !!productId,
  });
}

export function useCatalogPriceHistory(productId: number, days?: number) {
  return useQuery({
    queryKey: ['catalog', productId, 'price-history', days ?? null],
    queryFn: () => catalogApi.getPriceHistory(productId, days).then((r) => r.data),
    enabled: !!productId,
  });
}

export function useCatalogSuggestions(
  params: CatalogSuggestionParams,
  options?: { enabled?: boolean },
) {
  return useQuery({
    queryKey: ['catalog', 'suggestions', params],
    queryFn: ({ signal }) =>
      catalogApi.suggestions(params, signal).then((response) => response.data),
    enabled: (options?.enabled ?? true) && params.q.trim().length >= 2,
    staleTime: 60_000,
    retry: false,
  });
}
