import { z } from 'zod';

export const registerRequestSchema = z.object({
  email: z.string().email(),
  username: z
    .string()
    .regex(/^[a-zA-Z0-9_.-]{3,32}$/, 'Логин: 3–32 символа, латиница, цифры, _ . -')
    .optional()
    .or(z.literal('')),
  password: z.string().min(6).max(128),
  full_name: z.string().min(1).max(255),
  phone: z.string().max(20).optional(),
  company: z.string().max(255).optional(),
});

export const loginRequestSchema = z.object({
  identifier: z.string().min(1).max(255),
  password: z.string(),
});

export const tokenResponseSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string(),
  token_type: z.string(),
});

export const passwordResetRequestSchema = z.object({
  email: z.string().email('Введите корректный email'),
});

export const passwordResetConfirmSchema = z
  .object({
    token: z.string().min(1),
    new_password: z.string().min(8, 'Минимум 8 символов').max(128),
    confirm_password: z.string(),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: 'Пароли не совпадают',
    path: ['confirm_password'],
  });

export const messageResponseSchema = z.object({
  detail: z.string(),
});

export const vkAuthorizeResponseSchema = z.object({
  authorize_url: z.string(),
  state: z.string(),
  expires_in: z.number(),
});

export const vkCallbackRequestSchema = z.object({
  code: z.string().min(1).max(1024),
  state: z.string().min(1).max(256),
});

export const vkAuthResponseSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string(),
  token_type: z.string(),
  created: z.boolean(),
});

export const refreshRequestSchema = z.object({
  refresh_token: z.string(),
});

export type RegisterRequest = z.infer<typeof registerRequestSchema>;
export type LoginRequest = z.infer<typeof loginRequestSchema>;
export type TokenResponse = z.infer<typeof tokenResponseSchema>;
export type RefreshRequest = z.infer<typeof refreshRequestSchema>;
export type PasswordResetRequest = z.infer<typeof passwordResetRequestSchema>;
export type PasswordResetConfirm = z.infer<typeof passwordResetConfirmSchema>;
export type MessageResponse = z.infer<typeof messageResponseSchema>;
export type VkAuthorizeResponse = z.infer<typeof vkAuthorizeResponseSchema>;
export type VkCallbackRequest = z.infer<typeof vkCallbackRequestSchema>;
export type VkAuthResponse = z.infer<typeof vkAuthResponseSchema>;
