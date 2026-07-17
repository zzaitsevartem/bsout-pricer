import { useMutation, useQueryClient } from '@tanstack/react-query';
import { paymentApi } from './service';
import type { PaymentCreateRequest } from './schema';

export function useSubscribe() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PaymentCreateRequest) => paymentApi.subscribe(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'subscription'] });
    },
  });
}

export function useCancelSubscription() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => paymentApi.cancel(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'subscription'] });
    },
  });
}
