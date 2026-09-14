import { api } from '@/shared/api/axios';
import type {
  UserUpdateRequest,
  UserResponse,
  SubscriptionResponse,
  SubscriptionCreateRequest,
  EmailChangeRequest,
  EmailChangeResponse,
  EmailChangeConfirmResponse,
  EmailChangeCancelResponse,
  EmailResendResponse,
} from './schema';

export const userApi = {
  getMe: () =>
    api.get<UserResponse>('/users/me'),

  updateMe: (data: UserUpdateRequest) =>
    api.patch<UserResponse>('/users/me', data),

  getSubscription: () =>
    api.get<SubscriptionResponse>('/users/me/subscription'),

  createSubscription: (data: SubscriptionCreateRequest) =>
    api.post<SubscriptionResponse>('/users/me/subscription', data),

  resendVerification: () =>
    api.post<EmailResendResponse>('/auth/email/resend'),

  requestEmailChange: (data: EmailChangeRequest) =>
    api.post<EmailChangeResponse>('/auth/email/change', data),

  confirmEmailChangeOld: (token: string) =>
    api.post<EmailChangeConfirmResponse>('/auth/email/change/confirm/old', {
      token,
    }),

  confirmEmailChangeNew: (token: string) =>
    api.post<EmailChangeConfirmResponse>('/auth/email/change/confirm/new', {
      token,
    }),

  freezeEmailChange: (token: string) =>
    api.post<{ frozen: boolean }>('/auth/email/change/freeze', {
      token,
    }),

  cancelEmailChange: () =>
    api.delete<EmailChangeCancelResponse>('/auth/email/change'),
};
