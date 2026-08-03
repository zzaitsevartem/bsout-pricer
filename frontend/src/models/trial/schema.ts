import { z } from 'zod';

export const trialStatusResponseSchema = z.object({
  available: z.boolean(),
  client_id: z.string(),
});

export const trialSearchRequestSchema = z.object({
  query: z.string().max(500).default(''),
});

export const trialSearchResponseSchema = z.object({
  results: z.array(z.unknown()),
  total: z.number(),
  page: z.number(),
  per_page: z.number(),
  query: z.string(),
});

export type TrialStatusResponse = z.infer<typeof trialStatusResponseSchema>;
export type TrialSearchRequest = z.infer<typeof trialSearchRequestSchema>;
export type TrialSearchResponse = z.infer<typeof trialSearchResponseSchema>;
