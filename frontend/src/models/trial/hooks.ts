import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { trialApi } from './service';

export function useTrialStatus() {
  return useQuery({
    queryKey: ['trial', 'status'],
    queryFn: () => trialApi.getStatus().then((r) => r.data),
    staleTime: Infinity,
    retry: false,
  });
}

export function useTrialSearch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (query: string) => trialApi.search(query).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trial', 'status'] });
    },
  });
}
