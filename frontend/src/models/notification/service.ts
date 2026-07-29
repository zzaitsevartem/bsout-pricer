import { z } from 'zod';
import { api } from '@/shared/api/axios';
import {
  notificationListResponseSchema,
  notificationResponseSchema,
  unreadCountResponseSchema,
} from './schema';
import type {
  NotificationListParams,
  NotificationListResponse,
  NotificationResponse,
  UnreadCountResponse,
} from './schema';

function checkContract(schema: z.ZodType, data: unknown, source: string): void {
  if (process.env.NODE_ENV === 'production') {
    return;
  }
  const result = schema.safeParse(data);
  if (!result.success) {
    console.warn(
      `[models/notification] ${source}: response does not match schema`,
      result.error.issues,
    );
  }
}

export const notificationApi = {
  list: (params?: NotificationListParams) =>
    api.get<NotificationListResponse>('/notifications', { params }).then((response) => {
      checkContract(notificationListResponseSchema, response.data, 'GET /notifications');
      return response;
    }),

  unreadCount: () =>
    api.get<UnreadCountResponse>('/notifications/unread-count').then((response) => {
      checkContract(unreadCountResponseSchema, response.data, 'GET /notifications/unread-count');
      return response;
    }),

  markRead: (notificationId: number) =>
    api.post<NotificationResponse>(`/notifications/${notificationId}/read`).then((response) => {
      checkContract(
        notificationResponseSchema,
        response.data,
        `POST /notifications/${notificationId}/read`,
      );
      return response;
    }),
};
