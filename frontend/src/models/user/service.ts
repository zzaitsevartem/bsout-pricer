import { api } from '@/shared/api/axios';
import type { UserUpdateRequest, UserResponse, SubscriptionResponse, SubscriptionCreateRequest } from './schema';

export const userApi = {
  getMe: () =>
    api.get<UserResponse>('/users/me'),

  updateMe: (data: UserUpdateRequest) =>
    api.patch<UserResponse>('/users/me', data),

  getSubscription: () =>
    api.get<SubscriptionResponse>('/users/me/subscription'),

  createSubscription: (data: SubscriptionCreateRequest) =>
    api.post<SubscriptionResponse>('/users/me/subscription', data),
};
