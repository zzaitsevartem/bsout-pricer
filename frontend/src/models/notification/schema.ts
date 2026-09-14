import { z } from 'zod';

export const notificationResponseSchema = z.object({
  id: z.number(),
  user_id: z.number(),
  tracked_product_id: z.number().nullable(),
  product_id: z.number().nullable(),
  type: z.string(),
  channel: z.string(),
  status: z.string(),
  title: z.string(),
  body: z.string(),
  old_price: z.string().nullable(),
  new_price: z.string().nullable(),
  error: z.string().nullable(),
  created_at: z.string(),
  sent_at: z.string().nullable(),
  read_at: z.string().nullable(),
  is_read: z.boolean(),
});

export const notificationListResponseSchema = z.object({
  results: z.array(notificationResponseSchema),
  total: z.number(),
  page: z.number(),
  per_page: z.number(),
});

export const unreadCountResponseSchema = z.object({
  unread_count: z.number(),
});

export const notificationListParamsSchema = z.object({
  unread: z.boolean().optional(),
  page: z.number().int().min(1).optional(),
  per_page: z.number().int().min(1).max(100).optional(),
});

export type NotificationResponse = z.infer<typeof notificationResponseSchema>;
export type NotificationListResponse = z.infer<typeof notificationListResponseSchema>;
export type UnreadCountResponse = z.infer<typeof unreadCountResponseSchema>;
export type NotificationListParams = z.infer<typeof notificationListParamsSchema>;
