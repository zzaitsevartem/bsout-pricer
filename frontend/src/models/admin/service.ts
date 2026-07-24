import { api } from '@/shared/api/axios';
import type { AdminStatsResponse, UserBriefResponse } from './schema';

export const adminApi = {
  getStats: () =>
    api.get<AdminStatsResponse>('/admin/stats'),

  getUsers: (skip = 0, limit = 100) =>
    api.get<UserBriefResponse[]>('/admin/users', { params: { skip, limit } }),

  getUserById: (id: number) =>
    api.get<UserBriefResponse>(`/admin/users/${id}`),

  toggleUserActive: (id: number) =>
    api.post(`/admin/users/${id}/toggle-active`),
};
