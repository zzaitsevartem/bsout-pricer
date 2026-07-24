import { z } from 'zod';

export const categoryResponseSchema = z.object({
  id: z.number(),
  name: z.string(),
  slug: z.string(),
  created_at: z.string(),
});

export const categoryCreateRequestSchema = z.object({
  name: z.string().min(1).max(255),
  slug: z.string().min(1).max(100).regex(/^[a-z0-9_-]+$/),
});

export const categoryUpdateRequestSchema = z.object({
  name: z.string().min(1).max(255).optional(),
  slug: z.string().min(1).max(100).regex(/^[a-z0-9_-]+$/).optional(),
});

export type CategoryResponse = z.infer<typeof categoryResponseSchema>;
export type CategoryCreateRequest = z.infer<typeof categoryCreateRequestSchema>;
export type CategoryUpdateRequest = z.infer<typeof categoryUpdateRequestSchema>;
