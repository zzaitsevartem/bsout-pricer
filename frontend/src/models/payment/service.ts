import { api } from '@/shared/api/axios';
import type { PaymentCreateRequest, PaymentResponse } from './schema';

export const paymentApi = {
  subscribe: (data: PaymentCreateRequest) =>
    api.post<PaymentResponse>('/payment/subscribe', data),

  cancel: () =>
    api.post('/payment/cancel'),
};
