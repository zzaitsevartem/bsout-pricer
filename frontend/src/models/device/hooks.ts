import { useQuery } from '@tanstack/react-query';
import { deviceApi } from './service';
export function useDevice(key: string) {
  return useQuery({
    queryKey: ['device', key],
    queryFn: ({ signal }) => deviceApi.get(key, signal),
    retry: false,
  });
}
