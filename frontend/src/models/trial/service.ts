import { api } from '@/shared/api/axios';
import type { TrialStatusResponse, TrialSearchResponse } from './schema';

export const trialApi = {
  getStatus: () =>
    api.get<TrialStatusResponse>('/trial/status'),

  search: (query: string) =>
    api.post<TrialSearchResponse>('/trial/search', { query }),
};
