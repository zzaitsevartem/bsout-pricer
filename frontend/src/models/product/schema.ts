import { z } from 'zod';

export const storeRefSchema = z.object({
  id: z.number(),
  name: z.string(),
  slug: z.string(),
});

export const productResponseSchema = z.object({
  id: z.number(),
  store_id: z.number(),
  category_id: z.number().nullable(),
  external_id: z.string(),
  name: z.string(),
  description: z.string().nullable(),
  image_url: z.string().nullable(),
  price: z.string(),
  old_price: z.string().nullable(),
  currency: z.string(),
  in_stock: z.boolean(),
  product_url: z.string(),
  last_updated: z.string(),
  is_cheapest: z.boolean(),
  store: storeRefSchema.nullable(),
});

export const productSearchParamsSchema = z.object({
  q: z.string().max(500).default(''),
  store: z.string().optional(),
  category: z.string().optional(),
  min_price: z.string().optional(),
  max_price: z.string().optional(),
  in_stock: z.boolean().optional(),
  sort_by: z.string().default('price_asc'),
  page: z.number().min(1).default(1),
  per_page: z.number().min(1).max(100).default(20),
});

export const productListResponseSchema = z.object({
  results: z.array(productResponseSchema),
  total: z.number(),
  page: z.number(),
  per_page: z.number(),
});

export const priceHistoryResponseSchema = z.object({
  id: z.number(),
  product_id: z.number(),
  price: z.string(),
  recorded_at: z.string(),
});

export type StoreRef = z.infer<typeof storeRefSchema>;
export type ProductResponse = z.infer<typeof productResponseSchema>;
export type ProductSearchParams = z.infer<typeof productSearchParamsSchema>;
export type ProductListResponse = z.infer<typeof productListResponseSchema>;
export type PriceHistoryResponse = z.infer<typeof priceHistoryResponseSchema>;
