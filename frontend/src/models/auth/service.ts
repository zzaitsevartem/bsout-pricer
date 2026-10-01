import { api } from '@/shared/api/axios';
import type {
  RegisterRequest,
  LoginRequest,
  RefreshRequest,
  TokenResponse,
  PasswordResetRequest,
  PasswordResetConfirm,
  MessageResponse,
  VkAuthorizeResponse,
  VkCallbackRequest,
  VkAuthResponse,
} from './schema';

export const authApi = {
  register: (data: RegisterRequest) => api.post<TokenResponse>('/auth/register', data),

  login: (data: LoginRequest) => api.post<TokenResponse>('/auth/login', data),

  refresh: (data: RefreshRequest) => api.post<TokenResponse>('/auth/refresh', data),

  logout: () => api.post('/auth/logout'),

  confirmEmail: (token: string) =>
    api.post<{ email_verified: boolean; email_verified_at: string }>('/auth/email/confirm', {
      token,
    }),

  usernameAvailable: (username: string) =>
    api.get<{ available: boolean }>('/auth/username-available', { params: { username } }),

  requestPasswordReset: (data: PasswordResetRequest) =>
    api.post<MessageResponse>('/auth/password-reset/request', data),

  confirmPasswordReset: (data: Omit<PasswordResetConfirm, 'confirm_password'>) =>
    api.post<MessageResponse>('/auth/password-reset/confirm', data),

  vkAuthorize: (purpose: 'login' | 'link' = 'login') =>
    api.get<VkAuthorizeResponse>('/auth/vk/authorize', { params: { purpose } }),

  vkCallback: (data: VkCallbackRequest) => api.post<VkAuthResponse>('/auth/vk/callback', data),
};
