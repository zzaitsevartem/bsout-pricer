import { z } from 'zod';

export const searchHistoryResponseSchema = z.object({
  id: z.number(),
  user_id: z.number(),
  query: z.string(),
  filters: z.record(z.string(), z.unknown()).nullable(),
  results_count: z.number(),
  created_at: z.string(),
});

export type SearchHistoryResponse = z.infer<typeof searchHistoryResponseSchema>;
