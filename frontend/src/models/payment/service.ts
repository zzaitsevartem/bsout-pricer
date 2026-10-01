import { z } from 'zod';
import { api } from '@/shared/api/axios';
import {
  paymentListSchema,
  paymentSchema,
  planListSchema,
  subscriptionCancelResponseSchema,
} from './schema';
import type { PaymentCreateRequest } from './schema';

function parseResponse<T>(schema: z.ZodType<T>, data: unknown, source: string): T {
  const result = schema.safeParse(data);
  if (!result.success) {
    if (process.env.NODE_ENV !== 'production') {
      console.warn(`[models/payment] ${source}: response does not match schema`, result.error.issues);
    }
    throw new Error(`[models/payment] ${source}: unexpected response shape`);
  }
  return result.data;
}

export const paymentApi = {
  getPlans: () =>
    api
      .get('/payment/plans')
      .then((response) => parseResponse(planListSchema, response.data, 'GET /payment/plans')),

  getHistory: () =>
    api
      .get('/payment/history')
      .then((response) => parseResponse(paymentListSchema, response.data, 'GET /payment/history')),

  subscribe: (data: PaymentCreateRequest) =>
    api
      .post('/payment/subscribe', data)
      .then((response) => parseResponse(paymentSchema, response.data, 'POST /payment/subscribe')),

  cancel: () =>
    api
      .post('/payment/cancel')
      .then((response) =>
        parseResponse(subscriptionCancelResponseSchema, response.data, 'POST /payment/cancel'),
      ),
};
