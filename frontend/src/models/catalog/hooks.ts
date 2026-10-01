import { useQuery } from '@tanstack/react-query';
import { catalogApi } from './service';
import type { CatalogSearchParams } from './schema';

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
