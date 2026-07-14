import { z } from 'zod';
import { planEnumSchema } from '../user/schema';

export const paymentCreateRequestSchema = z.object({
  plan: planEnumSchema,
  payment_method: z.string().max(50).default('card'),
});

export const paymentResponseSchema = z.object({
  id: z.number(),
  user_id: z.number(),
  amount: z.string(),
  plan: planEnumSchema,
  status: z.string(),
  created_at: z.string(),
});

export const subscriptionUpgradeRequestSchema = z.object({
  plan: planEnumSchema,
});

export type PaymentCreateRequest = z.infer<typeof paymentCreateRequestSchema>;
export type PaymentResponse = z.infer<typeof paymentResponseSchema>;
export type SubscriptionUpgradeRequest = z.infer<typeof subscriptionUpgradeRequestSchema>;
