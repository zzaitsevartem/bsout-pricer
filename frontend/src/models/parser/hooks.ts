import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { parserApi } from './service';
import type { ParserRunRequest } from './schema';

export function useParsers() {
  return useQuery({
    queryKey: ['admin', 'parsers'],
    queryFn: () => parserApi.list().then((r) => r.data),
  });
}

export function useRunParser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ParserRunRequest) => parserApi.run(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'parsers'] });
    },
  });
}
