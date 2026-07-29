import { useQuery, type UseQueryOptions } from '@tanstack/react-query';
import { productApi } from './service';
import type { ProductSearchParams, ProductListResponse } from './schema';

export function useProductSearch(
  params: ProductSearchParams,
  options?: Partial<UseQueryOptions<ProductListResponse>>,
) {
  return useQuery({
    queryKey: ['products', 'search', params],
    queryFn: () => productApi.search(params).then((r) => r.data),
    ...options,
  });
}

export function useProduct(id: number) {
  return useQuery({
    queryKey: ['products', id],
    queryFn: () => productApi.getById(id).then((r) => r.data),
    enabled: !!id,
  });
}

export function usePriceHistory(productId: number) {
  return useQuery({
    queryKey: ['products', productId, 'price-history'],
    queryFn: () => productApi.getPriceHistory(productId).then((r) => r.data),
    enabled: !!productId,
  });
}
