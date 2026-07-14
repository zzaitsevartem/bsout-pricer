import { api } from '@/shared/api/axios';
import type { SearchHistoryResponse } from './schema';

export const searchApi = {
  getHistory: () =>
    api.get<SearchHistoryResponse[]>('/search/history'),
};
