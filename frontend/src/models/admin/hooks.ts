import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from './service';

export function useAdminStats() {
  return useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: () => adminApi.getStats().then((r) => r.data),
  });
}

export function useAdminUsers(skip = 0, limit = 100) {
  return useQuery({
    queryKey: ['admin', 'users', skip, limit],
    queryFn: () => adminApi.getUsers(skip, limit).then((r) => r.data),
  });
}

export function useAdminUser(id: number) {
  return useQuery({
    queryKey: ['admin', 'users', id],
    queryFn: () => adminApi.getUserById(id).then((r) => r.data),
    enabled: !!id,
  });
}

export function useToggleUserActive() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => adminApi.toggleUserActive(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
}
