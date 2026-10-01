import { z } from 'zod';

export const EXPORT_FEATURE_UNAVAILABLE = 'feature_unavailable';
export const EXPORT_SUBSCRIPTION_REQUIRED = 'subscription_required';

export const exportCatalogParamsSchema = z.object({
  q: z.string().max(500).optional(),
  device_id: z.number().int().min(1).optional(),
  part_type_id: z.number().int().min(1).optional(),
  quality_tier_id: z.number().int().min(1).optional(),
  sort_by: z.string().optional(),
  limit: z.number().int().min(1).max(10000).optional(),
});

export const exportErrorDetailSchema = z.object({
  code: z.string(),
  message: z.string(),
});

export const exportErrorBodySchema = z.object({
  detail: z.union([exportErrorDetailSchema, z.string()]),
});

export type ExportCatalogParams = z.infer<typeof exportCatalogParamsSchema>;
export type ExportErrorDetail = z.infer<typeof exportErrorDetailSchema>;
export type ExportErrorBody = z.infer<typeof exportErrorBodySchema>;

export type ExportedFile = {
  blob: Blob;
  filename: string;
};

export type ExportError = Error & {
  code: string;
  status: number;
};
