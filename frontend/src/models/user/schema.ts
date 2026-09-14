import { z } from 'zod';

export const planEnumSchema = z.enum(['trial', 'basic', 'advanced']);

export const userResponseSchema = z.object({
  id: z.number(),
  email: z.string(),
  username: z.string().nullable(),
  full_name: z.string(),
  phone: z.string().nullable(),
  company: z.string().nullable(),
  is_active: z.boolean(),
  is_admin: z.boolean(),
  email_verified_at: z.string().nullable(),
  pending_email: z.string().nullable(),
  email_change_old_confirmed_at: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const emailChangeRequestSchema = z.object({
  new_email: z.string().email().max(255),
});

export const emailChangeResponseSchema = z.object({
  sent: z.boolean(),
  expires_at: z.string(),
  new_email: z.string(),
});

export const emailChangeConfirmResponseSchema = z.object({
  status: z.string(),
  email_verified_at: z.string().nullable(),
});

export const emailChangeCancelResponseSchema = z.object({
  email: z.string(),
});

export const emailResendResponseSchema = z.object({
  sent: z.boolean(),
  expires_at: z.string(),
});

export const userUpdateRequestSchema = z.object({
  full_name: z.string().min(1).max(255).optional(),
  phone: z.string().max(20).optional(),
  company: z.string().max(255).optional(),
  username: z
    .string()
    .regex(/^[a-zA-Z0-9_.-]{3,32}$/, 'Логин: 3–32 символа, латиница, цифры, _ . -')
    .optional()
    .or(z.literal('')),
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
export type EmailChangeRequest = z.infer<typeof emailChangeRequestSchema>;
export type EmailChangeResponse = z.infer<typeof emailChangeResponseSchema>;
export type EmailChangeConfirmResponse = z.infer<typeof emailChangeConfirmResponseSchema>;
export type EmailChangeCancelResponse = z.infer<typeof emailChangeCancelResponseSchema>;
export type EmailResendResponse = z.infer<typeof emailResendResponseSchema>;
