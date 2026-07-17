import { api } from '@/shared/api/axios';
import type { StoreResponse, StoreCreateRequest, StoreUpdateRequest } from './schema';

export const storeApi = {
  getAll: () =>
    api.get<StoreResponse[]>('/stores'),

  getById: (id: number) =>
    api.get<StoreResponse>(`/stores/${id}`),

  create: (data: StoreCreateRequest) =>
    api.post<StoreResponse>('/stores', data),

  update: (id: number, data: StoreUpdateRequest) =>
    api.patch<StoreResponse>(`/stores/${id}`, data),
};
