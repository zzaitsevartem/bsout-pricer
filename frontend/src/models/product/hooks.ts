import { useQuery } from '@tanstack/react-query';
import { productApi } from './service';
import type { ProductSearchParams } from './schema';

export function useProductSearch(params: ProductSearchParams) {
  return useQuery({
    queryKey: ['products', 'search', params],
    queryFn: () => productApi.search(params).then((r) => r.data),
  });
}

export function useProduct(offerId: number) {
  return useQuery({
    queryKey: ['products', offerId],
    queryFn: () => productApi.getById(offerId).then((r) => r.data),
    enabled: !!offerId,
  });
}

export function usePriceHistory(offerId: number) {
  return useQuery({
    queryKey: ['products', offerId, 'price-history'],
    queryFn: () => productApi.getPriceHistory(offerId).then((r) => r.data),
    enabled: !!offerId,
  });
}
