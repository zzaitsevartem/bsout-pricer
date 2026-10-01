import { z } from 'zod';

export const STOCK_STATUSES = ['in_stock', 'low', 'out', 'preorder', 'unknown'] as const;
export const PRODUCT_SORT_OPTIONS = ['price_asc', 'price_desc', 'date'] as const;

export type StockStatus = (typeof STOCK_STATUSES)[number];
export type ProductSortOption = (typeof PRODUCT_SORT_OPTIONS)[number];

export const storeRefSchema = z.object({
  id: z.number(),
  name: z.string(),
  slug: z.string(),
});

export const productResponseSchema = z.object({
  id: z.number(),
  store_id: z.number(),
  category_id: z.number().nullable(),
  product_id: z.number().nullable(),
  source_sku: z.string(),
  title: z.string(),
  description: z.string().nullable(),
  image_url: z.string().nullable(),
  price_retail: z.string(),
  price_opt: z.string().nullable(),
  price_old: z.string().nullable(),
  currency: z.string(),
  stock_status: z.string(),
  stock_qty: z.number().nullable(),
  url: z.string(),
  last_seen_at: z.string(),
  is_cheapest: z.boolean(),
  store: storeRefSchema.nullable(),
});

export const productListResponseSchema = z.object({
  results: z.array(productResponseSchema),
  total: z.number(),
  page: z.number(),
  per_page: z.number(),
});

export const productSearchParamsSchema = z.object({
  q: z.string().max(500).optional(),
  store: z.string().optional(),
  category: z.string().optional(),
  min_price: z.number().optional(),
  max_price: z.number().optional(),
  in_stock: z.boolean().optional(),
  sort_by: z.string().optional(),
  page: z.number().int().min(1).optional(),
  per_page: z.number().int().min(1).max(100).optional(),
});

export const priceHistoryResponseSchema = z.object({
  id: z.number(),
  offer_id: z.number(),
  price_retail: z.string(),
  price_opt: z.string().nullable(),
  stock_status: z.string(),
  recorded_at: z.string(),
});

export const priceHistoryListResponseSchema = z.array(priceHistoryResponseSchema);

export type StoreRef = z.infer<typeof storeRefSchema>;
export type ProductResponse = z.infer<typeof productResponseSchema>;
export type ProductListResponse = z.infer<typeof productListResponseSchema>;
export type ProductSearchParams = z.infer<typeof productSearchParamsSchema>;
export type PriceHistoryResponse = z.infer<typeof priceHistoryResponseSchema>;
