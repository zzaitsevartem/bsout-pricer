import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { notificationApi } from './service';
import type { NotificationListParams } from './schema';

export const notificationKeys = {
  all: ['notifications'] as const,
  list: (params?: NotificationListParams) => ['notifications', 'list', params ?? null] as const,
  unreadCount: ['notifications', 'unread-count'] as const,
};

export function useNotifications(
  params?: NotificationListParams,
  options?: { enabled?: boolean },
) {
  return useQuery({
    queryKey: notificationKeys.list(params),
    queryFn: () => notificationApi.list(params).then((r) => r.data),
    enabled: options?.enabled ?? true,
    retry: false,
  });
}

export function useUnreadNotificationCount(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: notificationKeys.unreadCount,
    queryFn: () => notificationApi.unreadCount().then((r) => r.data),
    enabled: options?.enabled ?? true,
    retry: false,
  });
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (notificationId: number) =>
      notificationApi.markRead(notificationId).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });
}
