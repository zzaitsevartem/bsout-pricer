import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userApi } from './service';
import type { UserUpdateRequest, SubscriptionCreateRequest } from './schema';

export function useMe() {
  return useQuery({
    queryKey: ['user', 'me'],
    queryFn: () => userApi.getMe().then((r) => r.data),
  });
}

export function useUpdateMe() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UserUpdateRequest) => userApi.updateMe(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'me'] });
    },
  });
}

export function useSubscription() {
  return useQuery({
    queryKey: ['user', 'subscription'],
    queryFn: () => userApi.getSubscription().then((r) => r.data),
  });
}

export function useCreateSubscription() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SubscriptionCreateRequest) => userApi.createSubscription(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'subscription'] });
    },
  });
}
