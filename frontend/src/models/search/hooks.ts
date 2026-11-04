import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { searchApi } from './service';

export function useSearchHistory() {
  return useQuery({
    queryKey: ['search', 'history'],
    queryFn: () => searchApi.getHistory().then((r) => r.data),
  });
}

export function useClearSearchHistory() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => searchApi.clearHistory(),
    onSuccess: async () => {
      await client.cancelQueries({ queryKey: ['search', 'history'] });
      client.setQueryData(['search', 'history'], []);
      await client.invalidateQueries({ queryKey: ['search', 'history'] });
    },
  });
}
