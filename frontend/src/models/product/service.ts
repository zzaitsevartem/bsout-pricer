import { z } from 'zod';
import { api } from '@/shared/api/axios';
import {
  priceHistoryListResponseSchema,
  productListResponseSchema,
  productResponseSchema,
} from './schema';
import type {
  PriceHistoryResponse,
  ProductListResponse,
  ProductResponse,
  ProductSearchParams,
} from './schema';

function checkContract(schema: z.ZodType, data: unknown, source: string): void {
  if (process.env.NODE_ENV === 'production') {
    return;
  }
  const result = schema.safeParse(data);
  if (!result.success) {
    console.warn(`[models/product] ${source}: response does not match schema`, result.error.issues);
  }
}

export const productApi = {
  search: (params: ProductSearchParams) =>
    api.get<ProductListResponse>('/products', { params }).then((response) => {
      checkContract(productListResponseSchema, response.data, 'GET /products');
      return response;
    }),

  getById: (id: number) =>
    api.get<ProductResponse>(`/products/${id}`).then((response) => {
      checkContract(productResponseSchema, response.data, `GET /products/${id}`);
      return response;
    }),

  getPriceHistory: (id: number) =>
    api.get<PriceHistoryResponse[]>(`/products/${id}/price-history`).then((response) => {
      checkContract(
        priceHistoryListResponseSchema,
        response.data,
        `GET /products/${id}/price-history`,
      );
      return response;
    }),
};
