import { z } from 'zod';

export const parserRunRequestSchema = z.object({
  store_slug: z.string().min(1),
  full_sync: z.boolean().optional(),
});

export const parserStatusResponseSchema = z.object({
  store_slug: z.string(),
  is_running: z.boolean(),
  last_run: z.string().nullable(),
  products_found: z.number(),
  errors: z.array(z.string()),
});

export const parserRunResponseSchema = z.object({
  store_slug: z.string(),
  status: z.string(),
  upserted: z.number(),
});

export type ParserRunRequest = z.infer<typeof parserRunRequestSchema>;
export type ParserStatusResponse = z.infer<typeof parserStatusResponseSchema>;
export type ParserRunResponse = z.infer<typeof parserRunResponseSchema>;
