import { api } from '@/shared/api/axios';
import type { PlanResponse } from './schema';

export const planApi = {
  list: () => api.get<PlanResponse[]>('/plans').then((r) => r.data),
};
