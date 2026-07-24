import { z } from 'zod';

export const planEnumSchema = z.enum(['trial', 'basic', 'advanced']);

export const userResponseSchema = z.object({
  id: z.number(),
  email: z.string(),
  full_name: z.string(),
  phone: z.string().nullable(),
  company: z.string().nullable(),
  is_active: z.boolean(),
  is_admin: z.boolean(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const userUpdateRequestSchema = z.object({
  full_name: z.string().min(1).max(255).optional(),
  phone: z.string().max(20).optional(),
  company: z.string().max(255).optional(),
});

export const subscriptionResponseSchema = z.object({
  id: z.number(),
  user_id: z.number(),
  plan: planEnumSchema,
  start_date: z.string(),
  end_date: z.string(),
  is_active: z.boolean(),
  auto_renew: z.boolean(),
});

export const subscriptionCreateRequestSchema = z.object({
  plan: planEnumSchema,
});

export type Plan = z.infer<typeof planEnumSchema>;
export type UserResponse = z.infer<typeof userResponseSchema>;
export type UserUpdateRequest = z.infer<typeof userUpdateRequestSchema>;
export type SubscriptionResponse = z.infer<typeof subscriptionResponseSchema>;
export type SubscriptionCreateRequest = z.infer<typeof subscriptionCreateRequestSchema>;
