import { z } from 'zod';

export const planResponseSchema = z.object({
  slug: z.string(),
  name: z.string(),
  price: z.string(),
  period: z.string(),
  discount: z.string().nullable(),
  featured: z.boolean(),
  features: z.array(z.string()),
  tooltips: z.array(z.string()),
});

export type PlanResponse = z.infer<typeof planResponseSchema>;
