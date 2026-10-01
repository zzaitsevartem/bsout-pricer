import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userApi } from './service';
import type {
  UserUpdateRequest,
  SubscriptionCreateRequest,
  EmailChangeRequest,
} from './schema';

export function useMe(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['user', 'me'],
    queryFn: () => userApi.getMe().then((r) => r.data),
    enabled: options?.enabled ?? true,
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

export function useResendVerification() {
  return useMutation({
    mutationFn: () => userApi.resendVerification().then((r) => r.data),
  });
}

export function useRequestEmailChange() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: EmailChangeRequest) => userApi.requestEmailChange(data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'me'] });
    },
  });
}

export function useConfirmEmailChangeOld() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (token: string) => userApi.confirmEmailChangeOld(token).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'me'] });
    },
  });
}

export function useConfirmEmailChangeNew() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (token: string) => userApi.confirmEmailChangeNew(token).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'me'] });
    },
  });
}

export function useFreezeEmailChange() {
  return useMutation({
    mutationFn: (token: string) => userApi.freezeEmailChange(token).then((r) => r.data),
  });
}

export function useCancelEmailChange() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => userApi.cancelEmailChange().then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'me'] });
    },
  });
}

export function useSubscription() {
  return useQuery({
    queryKey: ['user', 'subscription'],
    queryFn: () => userApi.getSubscription().then((r) => r.data),
    retry: false,
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
