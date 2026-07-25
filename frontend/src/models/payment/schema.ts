import { z } from 'zod';
import { planEnumSchema } from '@/models/user/schema';

function toCamelKey(key: string): string {
  return key.replace(/_([a-z0-9])/g, (_match, char: string) => char.toUpperCase());
}

export function camelizeKeys(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(camelizeKeys);
  }
  if (value !== null && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, item]) => [
        toCamelKey(key),
        camelizeKeys(item),
      ]),
    );
  }
  return value;
}

const moneySchema = z.coerce.number();

export const paymentStatusSchema = z.enum(['pending', 'succeeded', 'canceled', 'failed']);

export const planSchema = z.preprocess(
  camelizeKeys,
  z.object({
    plan: planEnumSchema,
    nameRu: z.string(),
    price: moneySchema,
    firstPaymentPrice: moneySchema,
    currency: z.string(),
    durationDays: z.number(),
    trackedProducts: z.number(),
    stores: z.number(),
    fuzzySearch: z.boolean(),
    priceAlerts: z.boolean(),
    exportReports: z.boolean(),
    supportRu: z.string(),
  }),
);

export const planListSchema = z.array(planSchema);

export const paymentSchema = z.preprocess(
  camelizeKeys,
  z.object({
    id: z.number(),
    userId: z.number(),
    amount: moneySchema,
    currency: z.string(),
    plan: planEnumSchema,
    status: z.string(),
    provider: z.string(),
    providerPaymentId: z.string().nullish(),
    confirmationUrl: z.string().nullish(),
    description: z.string().nullish(),
    subscriptionId: z.number().nullish(),
    createdAt: z.string(),
    paidAt: z.string().nullish(),
  }),
);

export const paymentListSchema = z.array(paymentSchema);

export const subscriptionCancelResponseSchema = z.preprocess(
  camelizeKeys,
  z.object({
    detail: z.string(),
    subscriptionId: z.number(),
    plan: planEnumSchema,
    isActive: z.boolean(),
    autoRenew: z.boolean(),
    endDate: z.string(),
    accessUntil: z.string(),
  }),
);

export const paymentCreateRequestSchema = z.object({
  plan: planEnumSchema,
  payment_method: z.string().max(50).default('card'),
  idempotence_key: z.string().max(128).optional(),
});

export const subscriptionUpgradeRequestSchema = z.object({
  plan: planEnumSchema,
});

export type PaymentStatus = z.infer<typeof paymentStatusSchema>;
export type PlanResponse = z.infer<typeof planSchema>;
export type PaymentResponse = z.infer<typeof paymentSchema>;
export type SubscriptionCancelResponse = z.infer<typeof subscriptionCancelResponseSchema>;
export type PaymentCreateRequest = z.input<typeof paymentCreateRequestSchema>;
export type SubscriptionUpgradeRequest = z.infer<typeof subscriptionUpgradeRequestSchema>;
