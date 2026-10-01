import { describe, expect, it } from 'vitest';

import { feedbackRequestSchema } from './schema';

describe('feedbackRequestSchema', () => {
  it('accepts a valid message', () => {
    const parsed = feedbackRequestSchema.safeParse({
      name: 'Ivan',
      email: 'ivan@example.com',
      subject: 'Вопрос',
      message: 'Здравствуйте!',
    });
    expect(parsed.success).toBe(true);
  });

  it('rejects an invalid email', () => {
    const parsed = feedbackRequestSchema.safeParse({
      name: 'Ivan',
      email: 'not-an-email',
      subject: 'Вопрос',
      message: 'Здравствуйте!',
    });
    expect(parsed.success).toBe(false);
  });

  it('rejects an empty message', () => {
    const parsed = feedbackRequestSchema.safeParse({
      name: 'Ivan',
      email: 'ivan@example.com',
      subject: 'Вопрос',
      message: '',
    });
    expect(parsed.success).toBe(false);
  });
});
