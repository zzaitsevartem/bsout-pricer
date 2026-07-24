import { api } from '@/shared/api/axios';
import type { CategoryResponse, CategoryCreateRequest, CategoryUpdateRequest } from './schema';

export const categoryApi = {
  getAll: () =>
    api.get<CategoryResponse[]>('/categories'),

  getById: (id: number) =>
    api.get<CategoryResponse>(`/categories/${id}`),

  create: (data: CategoryCreateRequest) =>
    api.post<CategoryResponse>('/categories', data),

  update: (id: number, data: CategoryUpdateRequest) =>
    api.patch<CategoryResponse>(`/categories/${id}`, data),
};
