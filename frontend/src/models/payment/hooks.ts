import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { paymentApi } from './service';
import type { PaymentCreateRequest } from './schema';

export function usePlans() {
  return useQuery({
    queryKey: ['payment', 'plans'],
    queryFn: () => paymentApi.getPlans(),
    staleTime: 5 * 60 * 1000,
  });
}

export function usePaymentHistory(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['payment', 'history'],
    queryFn: () => paymentApi.getHistory(),
    enabled: options?.enabled ?? true,
    retry: false,
  });
}

export function useSubscribe() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PaymentCreateRequest) => paymentApi.subscribe(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payment', 'history'] });
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
      queryClient.invalidateQueries({ queryKey: ['payment', 'history'] });
    },
  });
}
