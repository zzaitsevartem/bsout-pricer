import { z } from 'zod';
import { storeRefSchema } from '@/models/product';

export const CATALOG_SORT_OPTIONS = ['min_price_asc', 'min_price_desc'] as const;
export const MATCH_STATUSES = ['unmatched', 'auto', 'manual', 'rejected'] as const;

export type CatalogSortOption = (typeof CATALOG_SORT_OPTIONS)[number];
export type MatchStatus = (typeof MATCH_STATUSES)[number];

export const brandRefSchema = z.object({
  id: z.number(),
  name: z.string(),
  slug: z.string(),
});

export const deviceRefSchema = z.object({
  id: z.number(),
  name: z.string(),
  model_key: z.string(),
  brand_id: z.number(),
});

export const partTypeRefSchema = z.object({
  id: z.number(),
  code: z.string(),
  name_ru: z.string(),
});

export const qualityTierRefSchema = z.object({
  id: z.number(),
  code: z.string(),
  name_ru: z.string(),
  rank: z.number(),
});

export const clusterRefSchema = z.object({
  id: z.number(),
  device_id: z.number(),
  part_type_id: z.number(),
  offers_count: z.number(),
  min_price_retail: z.string().nullable(),
  min_price_opt: z.string().nullable(),
});

export const catalogItemResponseSchema = z.object({
  id: z.number(),
  canonical_key: z.string(),
  canonical_name: z.string(),
  cluster_id: z.number().nullable(),
  key_attrs: z.record(z.string(), z.unknown()).nullable(),
  brand: brandRefSchema.nullable(),
  device: deviceRefSchema.nullable(),
  part_type: partTypeRefSchema.nullable(),
  quality_tier: qualityTierRefSchema.nullable(),
  min_price_retail: z.string().nullable(),
  min_price_opt: z.string().nullable(),
  offers_count: z.number(),
  stores_count: z.number(),
  store_slugs: z.array(z.string()),
});

export const catalogListResponseSchema = z.object({
  results: z.array(catalogItemResponseSchema),
  total: z.number(),
  page: z.number(),
  per_page: z.number(),
});

export const catalogSearchParamsSchema = z.object({
  q: z.string().max(500).optional(),
  device_id: z.number().int().min(1).optional(),
  part_type_id: z.number().int().min(1).optional(),
  quality_tier_id: z.number().int().min(1).optional(),
  sort_by: z.string().optional(),
  page: z.number().int().min(1).optional(),
  per_page: z.number().int().min(1).max(100).optional(),
});

export const comparisonOfferResponseSchema = z.object({
  id: z.number(),
  store_id: z.number(),
  source_sku: z.string(),
  title: z.string(),
  price_retail: z.string(),
  price_opt: z.string().nullable(),
  price_old: z.string().nullable(),
  currency: z.string(),
  stock_status: z.string(),
  stock_qty: z.number().nullable(),
  url: z.string(),
  match_status: z.string(),
  match_confidence: z.string().nullable(),
  last_seen_at: z.string(),
  price_changed_at: z.string().nullable(),
  is_cheapest: z.boolean(),
  store: storeRefSchema.nullable(),
});

export const comparisonStatsResponseSchema = z.object({
  offers_count: z.number(),
  stores_count: z.number(),
  min_price_retail: z.string().nullable(),
  max_price_retail: z.string().nullable(),
  avg_price_retail: z.string().nullable(),
  min_price_opt: z.string().nullable(),
  spread_abs: z.string().nullable(),
  spread_pct: z.number().nullable(),
});

export const alternativeTierResponseSchema = z.object({
  product_id: z.number(),
  canonical_key: z.string(),
  canonical_name: z.string(),
  quality_tier: qualityTierRefSchema.nullable(),
  min_price_retail: z.string().nullable(),
  min_price_opt: z.string().nullable(),
  offers_count: z.number(),
  stores_count: z.number(),
});

export const comparisonDetailResponseSchema = z.object({
  product: catalogItemResponseSchema,
  cluster: clusterRefSchema.nullable(),
  offers: z.array(comparisonOfferResponseSchema),
  stats: comparisonStatsResponseSchema,
  alternatives: z.array(alternativeTierResponseSchema),
});

export const pricePointResponseSchema = z.object({
  day: z.string(),
  min_price_retail: z.string(),
  max_price_retail: z.string().nullable(),
  avg_price_retail: z.string().nullable(),
  stores_count: z.number(),
});

export const productPriceHistoryResponseSchema = z.object({
  product_id: z.number(),
  days: z.number(),
  points: z.array(pricePointResponseSchema),
});

export type BrandRef = z.infer<typeof brandRefSchema>;
export type DeviceRef = z.infer<typeof deviceRefSchema>;
export type PartTypeRef = z.infer<typeof partTypeRefSchema>;
export type QualityTierRef = z.infer<typeof qualityTierRefSchema>;
export type ClusterRef = z.infer<typeof clusterRefSchema>;
export type CatalogItemResponse = z.infer<typeof catalogItemResponseSchema>;
export type CatalogListResponse = z.infer<typeof catalogListResponseSchema>;
export type CatalogSearchParams = z.infer<typeof catalogSearchParamsSchema>;
export type ComparisonOfferResponse = z.infer<typeof comparisonOfferResponseSchema>;
export type ComparisonStatsResponse = z.infer<typeof comparisonStatsResponseSchema>;
export type AlternativeTierResponse = z.infer<typeof alternativeTierResponseSchema>;
export type ComparisonDetailResponse = z.infer<typeof comparisonDetailResponseSchema>;
export type PricePointResponse = z.infer<typeof pricePointResponseSchema>;
export type ProductPriceHistoryResponse = z.infer<typeof productPriceHistoryResponseSchema>;
