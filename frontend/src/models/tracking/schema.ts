import { z } from 'zod';

export const TRACKING_LIMIT_REACHED_CODE = 'tracking_limit_reached';
export const SUBSCRIPTION_REQUIRED_CODE = 'subscription_required';
export const FEATURE_UNAVAILABLE_CODE = 'feature_unavailable';

export const PLANS = ['trial', 'basic', 'advanced'] as const;

export type Plan = (typeof PLANS)[number];

export const trackedProductResponseSchema = z.object({
  id: z.number(),
  product_id: z.number(),
  canonical_key: z.string(),
  canonical_name: z.string(),
  target_price: z.string().nullable(),
  notify_on_any_drop: z.boolean(),
  is_active: z.boolean(),
  initial_price: z.string().nullable(),
  last_seen_price: z.string().nullable(),
  current_price: z.string().nullable(),
  price_delta: z.string().nullable(),
  price_delta_pct: z.number().nullable(),
  stores_count: z.number(),
  target_reached: z.boolean(),
  last_notified_at: z.string().nullable(),
  created_at: z.string(),
});

export const trackedProductListResponseSchema = z.object({
  results: z.array(trackedProductResponseSchema),
  total: z.number(),
  page: z.number(),
  per_page: z.number(),
});

export const trackingUsageResponseSchema = z.object({
  used: z.number(),
  limit: z.number(),
  remaining: z.number(),
  plan: z.enum(PLANS).nullable(),
});

export const trackedProductCreateRequestSchema = z.object({
  product_id: z.number().int().min(1),
  target_price: z.number().positive().optional(),
});

export const trackedProductUpdateRequestSchema = z.object({
  target_price: z.number().positive().nullable().optional(),
  notify_on_any_drop: z.boolean().optional(),
  is_active: z.boolean().optional(),
});

export const trackingListParamsSchema = z.object({
  is_active: z.boolean().optional(),
  page: z.number().int().min(1).optional(),
  per_page: z.number().int().min(1).max(100).optional(),
});

export const trackingLimitDetailSchema = z.object({
  code: z.literal(TRACKING_LIMIT_REACHED_CODE),
  limit: z.number(),
  used: z.number(),
  plan: z.string().nullable(),
  message: z.string(),
});

export type TrackedProductResponse = z.infer<typeof trackedProductResponseSchema>;
export type TrackedProductListResponse = z.infer<typeof trackedProductListResponseSchema>;
export type TrackingUsageResponse = z.infer<typeof trackingUsageResponseSchema>;
export type TrackedProductCreateRequest = z.infer<typeof trackedProductCreateRequestSchema>;
export type TrackedProductUpdateRequest = z.infer<typeof trackedProductUpdateRequestSchema>;
export type TrackingListParams = z.infer<typeof trackingListParamsSchema>;
export type TrackingLimitDetail = z.infer<typeof trackingLimitDetailSchema>;
