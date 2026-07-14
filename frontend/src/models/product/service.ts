import { api } from '@/shared/api/axios';
import type { ProductSearchParams, ProductListResponse, ProductResponse, PriceHistoryResponse } from './schema';

export const productApi = {
  search: (params: ProductSearchParams) =>
    api.get<ProductListResponse>('/products', { params }),

  getById: (id: number) =>
    api.get<ProductResponse>(`/products/${id}`),

  getPriceHistory: (id: number) =>
    api.get<PriceHistoryResponse[]>(`/products/${id}/price-history`),
};
