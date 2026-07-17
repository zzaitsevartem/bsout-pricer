import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { storeApi } from './service';
import type { StoreCreateRequest, StoreUpdateRequest } from './schema';

export function useStores() {
  return useQuery({
    queryKey: ['stores'],
    queryFn: () => storeApi.getAll().then((r) => r.data),
  });
}

export function useStore(id: number) {
  return useQuery({
    queryKey: ['stores', id],
    queryFn: () => storeApi.getById(id).then((r) => r.data),
    enabled: !!id,
  });
}

export function useCreateStore() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: StoreCreateRequest) => storeApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stores'] });
    },
  });
}

export function useUpdateStore() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: StoreUpdateRequest }) =>
      storeApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stores'] });
    },
  });
}
