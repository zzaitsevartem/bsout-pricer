import { z } from 'zod';

export const parserRunRequestSchema = z.object({
  store_slug: z.string().min(1),
  full_sync: z.boolean().default(false),
});

export const parserStatusResponseSchema = z.object({
  store_slug: z.string(),
  is_running: z.boolean(),
  last_run: z.string().nullable(),
  products_found: z.number(),
  errors: z.array(z.string()),
});

export type ParserRunRequest = z.infer<typeof parserRunRequestSchema>;
export type ParserStatusResponse = z.infer<typeof parserStatusResponseSchema>;
