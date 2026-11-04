import { z } from 'zod';
import { api } from '@/shared/api/axios';
import {
  facetOptionSchema,
  catalogListResponseSchema,
  catalogFacetsSchema,
  catalogSuggestionsSchema,
  comparisonDetailResponseSchema,
  productPriceHistoryResponseSchema,
} from './schema';
import type {
  CatalogListResponse,
  CatalogFacetsResponse,
  CatalogSuggestion,
  CatalogSuggestionParams,
  CatalogSearchParams,
  ComparisonDetailResponse,
  ProductPriceHistoryResponse,
} from './schema';

function checkContract(schema: z.ZodType, data: unknown, source: string): void {
  if (process.env.NODE_ENV === 'production') {
    return;
  }
  const result = schema.safeParse(data);
  if (!result.success) {
    console.warn(`[models/catalog] ${source}: response does not match schema`, result.error.issues);
  }
}

export const catalogApi = {
  devices: (params: { q: string; limit?: number }, signal?: AbortSignal) =>
    api.get<z.infer<typeof facetOptionSchema>[]>('/products/catalog/devices', { params, signal }).then((response) => {
      checkContract(z.array(facetOptionSchema), response.data, 'GET /products/catalog/devices');
      return response;
    }),
  facets: (params: CatalogSearchParams) =>
    api.get<CatalogFacetsResponse>('/products/catalog/facets', { params }).then((response) => {
      checkContract(catalogFacetsSchema, response.data, 'GET /products/catalog/facets');
      return response;
    }),
  suggestions: (params: CatalogSuggestionParams, signal?: AbortSignal) =>
    api
      .get<CatalogSuggestion[]>('/products/catalog/suggestions', { params, signal })
      .then((response) => {
        checkContract(catalogSuggestionsSchema, response.data, 'GET /products/catalog/suggestions');
        return response;
      }),

  search: (params: CatalogSearchParams) =>
    api.get<CatalogListResponse>('/products/catalog', { params }).then((response) => {
      checkContract(catalogListResponseSchema, response.data, 'GET /products/catalog');
      return response;
    }),

  getById: (productId: number) =>
    api.get<ComparisonDetailResponse>(`/products/catalog/${productId}`).then((response) => {
      checkContract(
        comparisonDetailResponseSchema,
        response.data,
        `GET /products/catalog/${productId}`,
      );
      return response;
    }),

  getPriceHistory: (productId: number, days?: number) =>
    api
      .get<ProductPriceHistoryResponse>(`/products/catalog/${productId}/price-history`, {
        params: { days },
      })
      .then((response) => {
        checkContract(
          productPriceHistoryResponseSchema,
          response.data,
          `GET /products/catalog/${productId}/price-history`,
        );
        return response;
      }),
};
