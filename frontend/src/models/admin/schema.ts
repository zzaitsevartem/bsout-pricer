import { z } from 'zod';

export const userBriefResponseSchema = z.object({
  id: z.number(),
  email: z.string(),
  full_name: z.string(),
  is_active: z.boolean(),
  is_admin: z.boolean(),
  created_at: z.string(),
});

export const adminStatsResponseSchema = z.object({
  total_users: z.number(),
  active_subscriptions: z.number(),
  total_products: z.number(),
  total_stores: z.number(),
});

export const offerImportItemSchema = z.object({
  store_slug: z.string().min(1).max(100),
  source_sku: z.string().min(1).max(255),
  title: z.string().min(1).max(500),
  price_retail: z.union([z.string(), z.number()]),
  price_opt: z.union([z.string(), z.number()]).nullable().optional(),
  price_old: z.union([z.string(), z.number()]).nullable().optional(),
  stock_status: z.string().optional(),
  stock_qty: z.number().nullable().optional(),
  url: z.string().max(1000).optional(),
  image_url: z.string().max(1000).nullable().optional(),
  description: z.string().nullable().optional(),
  category: z.string().max(255).nullable().optional(),
});

export const offerImportRowErrorSchema = z.object({
  index: z.number(),
  reason: z.string(),
  store_slug: z.string().nullable(),
  source_sku: z.string().nullable(),
});

export const offerImportResponseSchema = z.object({
  total: z.number(),
  created: z.number(),
  updated: z.number(),
  skipped: z.number(),
  errors: z.array(offerImportRowErrorSchema),
});

export const moderationStoreRefSchema = z.object({
  id: z.number(),
  name: z.string(),
  slug: z.string(),
});

export const moderationOfferRefSchema = z.object({
  id: z.number(),
  store_id: z.number(),
  source_sku: z.string(),
  title: z.string(),
  normalized_title: z.string(),
  price_retail: z.string(),
  price_opt: z.string().nullable(),
  price_old: z.string().nullable(),
  currency: z.string(),
  stock_status: z.string(),
  url: z.string(),
  image_url: z.string().nullable(),
  is_active: z.boolean(),
  product_id: z.number().nullable(),
  match_status: z.string(),
  match_confidence: z.string().nullable(),
  last_seen_at: z.string(),
  store: moderationStoreRefSchema.nullable(),
});

export const moderationProductRefSchema = z.object({
  id: z.number(),
  canonical_key: z.string(),
  canonical_name: z.string(),
  cluster_id: z.number().nullable(),
  brand_id: z.number().nullable(),
  quality_tier_id: z.number().nullable(),
  key_attrs: z.record(z.string(), z.unknown()).nullable(),
});

export const matchCandidateResponseSchema = z.object({
  id: z.number(),
  offer_id: z.number(),
  product_id: z.number(),
  score: z.string(),
  features: z.record(z.string(), z.unknown()).nullable(),
  status: z.string(),
  decided_by: z.number().nullable(),
  decided_at: z.string().nullable(),
  created_at: z.string(),
  offer: moderationOfferRefSchema.nullable(),
  product: moderationProductRefSchema.nullable(),
});

export const matchCandidateListResponseSchema = z.object({
  results: z.array(matchCandidateResponseSchema),
  total: z.number(),
  page: z.number(),
  per_page: z.number(),
});

export const matchCandidateStatusFilterSchema = z.enum([
  'pending',
  'approved',
  'rejected',
  'all',
]);

export const matchCandidateListParamsSchema = z.object({
  status: matchCandidateStatusFilterSchema.optional(),
  offer_id: z.number().min(1).optional(),
  product_id: z.number().min(1).optional(),
  page: z.number().min(1).optional(),
  per_page: z.number().min(1).max(100).optional(),
});

export const offerStateResponseSchema = z.object({
  id: z.number(),
  product_id: z.number().nullable(),
  match_status: z.string(),
  match_confidence: z.string().nullable(),
});

export const candidateDecisionResponseSchema = z.object({
  candidate: matchCandidateResponseSchema,
  offer: offerStateResponseSchema,
  rejected_candidate_ids: z.array(z.number()),
});

export const offerLinkRequestSchema = z.object({
  product_id: z.number().min(1),
});

export const broadcastAudienceSchema = z.enum([
  'all_active',
  'verified',
  'subscribers',
  'custom',
]);

export const broadcastStatusSchema = z.enum([
  'draft',
  'queued',
  'running',
  'completed',
  'failed',
  'cancelled',
]);

export const recipientStatusSchema = z.enum(['pending', 'sending', 'sent', 'failed']);

export const broadcastCreateRequestSchema = z.object({
  name: z.string().min(1).max(120),
  audience: broadcastAudienceSchema,
  subject: z.string().min(1).max(200),
  text: z.string().min(1).max(200000),
  html: z.string().max(500000).nullable().optional(),
  recipient_emails: z.array(z.string().email()).max(500).optional(),
});

export const broadcastResponseSchema = z.object({
  id: z.number(),
  name: z.string(),
  audience: broadcastAudienceSchema,
  subject: z.string(),
  text: z.string(),
  html: z.string().nullable(),
  status: broadcastStatusSchema,
  total_recipients: z.number(),
  sent_count: z.number(),
  failed_count: z.number(),
  error_summary: z.string().nullable(),
  created_at: z.string(),
  started_at: z.string().nullable(),
  finished_at: z.string().nullable(),
});

export const broadcastListResponseSchema = z.object({
  items: z.array(broadcastResponseSchema),
  total: z.number(),
  page: z.number(),
  per_page: z.number(),
});

export const broadcastPreviewRequestSchema = broadcastCreateRequestSchema;

export const broadcastPreviewResponseSchema = z.object({
  recipient_count: z.number(),
  sample_emails: z.array(z.string()),
});

export const broadcastSendTestResponseSchema = z.object({
  sent_to: z.string(),
});

export const broadcastRecipientItemResponseSchema = z.object({
  id: z.number(),
  user_id: z.number().nullable(),
  email: z.string(),
  status: recipientStatusSchema,
  error: z.string().nullable(),
  sent_at: z.string().nullable(),
  created_at: z.string(),
});

export const broadcastRecipientListResponseSchema = z.object({
  items: z.array(broadcastRecipientItemResponseSchema),
  total: z.number(),
  page: z.number(),
  per_page: z.number(),
});

export const offerLinkResponseSchema = z.object({
  offer: offerStateResponseSchema,
  rejected_candidate_ids: z.array(z.number()),
});

export type UserBriefResponse = z.infer<typeof userBriefResponseSchema>;
export type AdminStatsResponse = z.infer<typeof adminStatsResponseSchema>;
export type OfferImportItem = z.infer<typeof offerImportItemSchema>;
export type OfferImportRowError = z.infer<typeof offerImportRowErrorSchema>;
export type OfferImportResponse = z.infer<typeof offerImportResponseSchema>;
export type ModerationStoreRef = z.infer<typeof moderationStoreRefSchema>;
export type ModerationOfferRef = z.infer<typeof moderationOfferRefSchema>;
export type ModerationProductRef = z.infer<typeof moderationProductRefSchema>;
export type MatchCandidateResponse = z.infer<typeof matchCandidateResponseSchema>;
export type MatchCandidateListResponse = z.infer<typeof matchCandidateListResponseSchema>;
export type MatchCandidateStatusFilter = z.infer<typeof matchCandidateStatusFilterSchema>;
export type MatchCandidateListParams = z.infer<typeof matchCandidateListParamsSchema>;
export type OfferStateResponse = z.infer<typeof offerStateResponseSchema>;
export type CandidateDecisionResponse = z.infer<typeof candidateDecisionResponseSchema>;
export type OfferLinkRequest = z.infer<typeof offerLinkRequestSchema>;
export type OfferLinkResponse = z.infer<typeof offerLinkResponseSchema>;
export type BroadcastAudience = z.infer<typeof broadcastAudienceSchema>;
export type BroadcastStatus = z.infer<typeof broadcastStatusSchema>;
export type RecipientStatus = z.infer<typeof recipientStatusSchema>;
export type BroadcastCreateRequest = z.infer<typeof broadcastCreateRequestSchema>;
export type BroadcastResponse = z.infer<typeof broadcastResponseSchema>;
export type BroadcastListResponse = z.infer<typeof broadcastListResponseSchema>;
export type BroadcastPreviewResponse = z.infer<typeof broadcastPreviewResponseSchema>;
export type BroadcastSendTestResponse = z.infer<typeof broadcastSendTestResponseSchema>;
export type BroadcastRecipientItemResponse = z.infer<
  typeof broadcastRecipientItemResponseSchema
>;
export type BroadcastRecipientListResponse = z.infer<
  typeof broadcastRecipientListResponseSchema
>;
