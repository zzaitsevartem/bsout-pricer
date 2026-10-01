import { z } from 'zod';
import { api } from '@/shared/api/axios';
import { searchHistoryListResponseSchema } from './schema';
import type { SearchHistoryResponse } from './schema';

function checkContract(schema: z.ZodType, data: unknown, source: string): void {
  if (process.env.NODE_ENV === 'production') {
    return;
  }
  const result = schema.safeParse(data);
  if (!result.success) {
    console.warn(`[models/search] ${source}: response does not match schema`, result.error.issues);
  }
}

export const searchApi = {
  getHistory: () =>
    api.get<SearchHistoryResponse[]>('/search/history').then((response) => {
      checkContract(searchHistoryListResponseSchema, response.data, 'GET /search/history');
      return response;
    }),
};
