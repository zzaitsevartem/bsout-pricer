import { useQuery } from '@tanstack/react-query';
import { searchApi } from './service';

export function useSearchHistory() {
  return useQuery({
    queryKey: ['search', 'history'],
    queryFn: () => searchApi.getHistory().then((r) => r.data),
  });
}
