import { z } from 'zod';

export const registerRequestSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6).max(128),
  full_name: z.string().min(1).max(255),
  phone: z.string().max(20).optional(),
  company: z.string().max(255).optional(),
});

export const loginRequestSchema = z.object({
  email: z.string().email(),
  password: z.string(),
});

export const tokenResponseSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string(),
  token_type: z.string(),
});

export const refreshRequestSchema = z.object({
  refresh_token: z.string(),
});

export type RegisterRequest = z.infer<typeof registerRequestSchema>;
export type LoginRequest = z.infer<typeof loginRequestSchema>;
export type TokenResponse = z.infer<typeof tokenResponseSchema>;
export type RefreshRequest = z.infer<typeof refreshRequestSchema>;
