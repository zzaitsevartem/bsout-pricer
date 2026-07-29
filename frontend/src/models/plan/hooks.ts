import { useQuery, type UseQueryOptions } from '@tanstack/react-query';
import { planApi } from './service';
import type { PlanResponse } from './schema';

export function usePlans(options?: Partial<UseQueryOptions<PlanResponse[]>>) {
  return useQuery({
    queryKey: ['plans'],
    queryFn: () => planApi.list(),
    ...options,
  });
}
