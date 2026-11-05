import { z } from 'zod';
import { brandRefSchema } from '@/models/catalog';
export const deviceSchema = z.object({
  id: z.number(),
  model_key: z.string(),
  name: z.string(),
  brand: brandRefSchema,
  aliases: z.array(z.string()),
  model_codes: z.array(z.string()),
  release_year: z.number().nullable(),
  images: z.array(
    z.object({
      url: z.string(),
      source_name: z.string(),
      source_url: z.string(),
      license: z.string().nullable(),
      attribution: z.string().nullable(),
    }),
  ),
  metadata_source_url: z.string().nullable(),
});
export type Device = z.infer<typeof deviceSchema>;
