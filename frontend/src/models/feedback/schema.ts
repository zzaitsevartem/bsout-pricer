import { z } from 'zod';

export const feedbackRequestSchema = z.object({
  name: z.string().min(1, 'Укажите имя').max(100),
  email: z.string().email('Введите корректный email'),
  subject: z.string().min(1, 'Укажите тему').max(200),
  message: z.string().min(1, 'Напишите сообщение').max(5000),
});

export const feedbackResponseSchema = z.object({
  detail: z.string(),
});

export type FeedbackRequest = z.infer<typeof feedbackRequestSchema>;
export type FeedbackResponse = z.infer<typeof feedbackResponseSchema>;
