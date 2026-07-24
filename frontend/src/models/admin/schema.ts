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

export type UserBriefResponse = z.infer<typeof userBriefResponseSchema>;
export type AdminStatsResponse = z.infer<typeof adminStatsResponseSchema>;
