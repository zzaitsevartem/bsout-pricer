import { z } from 'zod';

export const storeResponseSchema = z.object({
  id: z.number(),
  name: z.string(),
  slug: z.string(),
  website_url: z.string(),
  logo_url: z.string().nullable(),
  is_active: z.boolean(),
  created_at: z.string(),
});

export const storeCreateRequestSchema = z.object({
  name: z.string().min(1).max(255),
  slug: z.string().min(1).max(100).regex(/^[a-z0-9_-]+$/),
  website_url: z.string().max(500),
  logo_url: z.string().max(500).optional(),
});

export const storeUpdateRequestSchema = z.object({
  name: z.string().min(1).max(255).optional(),
  slug: z.string().min(1).max(100).regex(/^[a-z0-9_-]+$/).optional(),
  website_url: z.string().max(500).optional(),
  logo_url: z.string().max(500).optional(),
  is_active: z.boolean().optional(),
});

export type StoreResponse = z.infer<typeof storeResponseSchema>;
export type StoreCreateRequest = z.infer<typeof storeCreateRequestSchema>;
export type StoreUpdateRequest = z.infer<typeof storeUpdateRequestSchema>;
