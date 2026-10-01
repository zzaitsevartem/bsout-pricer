import { describe, expect, it } from 'vitest';

import {
  loginRequestSchema,
  registerRequestSchema,
  tokenResponseSchema,
  passwordResetRequestSchema,
  passwordResetConfirmSchema,
  vkAuthorizeResponseSchema,
  vkCallbackRequestSchema,
  vkAuthResponseSchema,
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
  it('accepts identifier (email or username) + password', () => {
    expect(loginRequestSchema.safeParse({ identifier: 'a@b.com', password: 'x' }).success).toBe(
      true,
    );
    expect(loginRequestSchema.safeParse({ identifier: 'sugarfree', password: 'x' }).success).toBe(
      true,
    );
  });

  it('rejects a missing password', () => {
    expect(loginRequestSchema.safeParse({ identifier: 'a@b.com' }).success).toBe(false);
  });

  it('rejects a missing identifier', () => {
    expect(loginRequestSchema.safeParse({ password: 'x' }).success).toBe(false);
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

describe('passwordResetRequestSchema', () => {
  it('accepts a valid email', () => {
    expect(passwordResetRequestSchema.safeParse({ email: 'user@example.com' }).success).toBe(true);
  });

  it('rejects an invalid email', () => {
    expect(passwordResetRequestSchema.safeParse({ email: 'not-an-email' }).success).toBe(false);
  });
});

describe('passwordResetConfirmSchema', () => {
  it('accepts matching passwords of 8+ chars', () => {
    const parsed = passwordResetConfirmSchema.safeParse({
      token: 'tok',
      new_password: 's3cret-pass',
      confirm_password: 's3cret-pass',
    });
    expect(parsed.success).toBe(true);
  });

  it('rejects short passwords', () => {
    const parsed = passwordResetConfirmSchema.safeParse({
      token: 'tok',
      new_password: 'short',
      confirm_password: 'short',
    });
    expect(parsed.success).toBe(false);
  });

  it('rejects mismatched passwords', () => {
    const parsed = passwordResetConfirmSchema.safeParse({
      token: 'tok',
      new_password: 's3cret-pass',
      confirm_password: 'other-pass',
    });
    expect(parsed.success).toBe(false);
  });
});

describe('vkAuthorizeResponseSchema', () => {
  it('accepts the authorize payload', () => {
    const parsed = vkAuthorizeResponseSchema.safeParse({
      authorize_url: 'https://id.vk.com/authorize?x=1',
      state: 'abc',
      expires_in: 600,
    });
    expect(parsed.success).toBe(true);
  });
});

describe('vkCallbackRequestSchema', () => {
  it('accepts code + state', () => {
    const parsed = vkCallbackRequestSchema.safeParse({ code: 'c', state: 's' });
    expect(parsed.success).toBe(true);
  });

  it('rejects an empty code', () => {
    const parsed = vkCallbackRequestSchema.safeParse({ code: '', state: 's' });
    expect(parsed.success).toBe(false);
  });
});

describe('vkAuthResponseSchema (snake_case API contract)', () => {
  it('accepts tokens with the created flag', () => {
    const parsed = vkAuthResponseSchema.safeParse({
      access_token: 'a',
      refresh_token: 'r',
      token_type: 'bearer',
      created: false,
    });
    expect(parsed.success).toBe(true);
  });
});
