import { api } from '@/shared/api/axios';
import type { RegisterRequest, LoginRequest, RefreshRequest, TokenResponse } from './schema';

export const authApi = {
  register: (data: RegisterRequest) =>
    api.post<TokenResponse>('/auth/register', data),

  login: (data: LoginRequest) =>
    api.post<TokenResponse>('/auth/login', data),

  refresh: (data: RefreshRequest) =>
    api.post<TokenResponse>('/auth/refresh', data),

  logout: () =>
    api.post('/auth/logout'),
};
