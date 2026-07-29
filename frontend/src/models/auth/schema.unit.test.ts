import { describe, expect, it } from 'vitest';

import {
  loginRequestSchema,
  registerRequestSchema,
  tokenResponseSchema,
} from './schema';

describe('registerRequestSchema', () => {
  it('accepts a valid payload', () => {
    const parsed = registerRequestSchema.safeParse({
      email: 'user@example.com',
      password: 's3cret-pass',
      full_name: 'Ivan Petrov',
    });
    expect(parsed.success).toBe(true);
  });

  it('rejects passwords shorter than 6 chars', () => {
    const parsed = registerRequestSchema.safeParse({
      email: 'user@example.com',
      password: '123',
      full_name: 'Ivan',
    });
    expect(parsed.success).toBe(false);
  });

  it('rejects an invalid email', () => {
    const parsed = registerRequestSchema.safeParse({
      email: 'not-an-email',
      password: 's3cret-pass',
      full_name: 'Ivan',
    });
    expect(parsed.success).toBe(false);
  });

  it('requires a non-empty full_name', () => {
    const parsed = registerRequestSchema.safeParse({
      email: 'user@example.com',
      password: 's3cret-pass',
      full_name: '',
    });
    expect(parsed.success).toBe(false);
  });

  it('treats phone and company as optional', () => {
    const parsed = registerRequestSchema.safeParse({
      email: 'user@example.com',
      password: 's3cret-pass',
      full_name: 'Ivan',
    });
    expect(parsed.success && parsed.data.phone).toBeUndefined();
  });
});

describe('loginRequestSchema', () => {
  it('accepts email + password', () => {
    expect(
      loginRequestSchema.safeParse({ email: 'a@b.com', password: 'x' }).success,
    ).toBe(true);
  });

  it('rejects a missing password', () => {
    expect(loginRequestSchema.safeParse({ email: 'a@b.com' }).success).toBe(false);
  });
});

describe('tokenResponseSchema (snake_case API contract)', () => {
  it('accepts snake_case token fields', () => {
    const parsed = tokenResponseSchema.safeParse({
      access_token: 'a',
      refresh_token: 'r',
      token_type: 'bearer',
    });
    expect(parsed.success).toBe(true);
  });

  it('rejects camelCase token fields', () => {
    const parsed = tokenResponseSchema.safeParse({
      accessToken: 'a',
      refreshToken: 'r',
      tokenType: 'bearer',
    });
    expect(parsed.success).toBe(false);
  });
});
