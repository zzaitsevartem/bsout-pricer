import { z } from 'zod';
import { api } from '@/shared/api/axios';
import {
  trackedProductListResponseSchema,
  trackedProductResponseSchema,
  trackingUsageResponseSchema,
} from './schema';
import type {
  TrackedProductCreateRequest,
  TrackedProductListResponse,
  TrackedProductResponse,
  TrackedProductUpdateRequest,
  TrackingListParams,
  TrackingUsageResponse,
} from './schema';

function checkContract(schema: z.ZodType, data: unknown, source: string): void {
  if (process.env.NODE_ENV === 'production') {
    return;
  }
  const result = schema.safeParse(data);
  if (!result.success) {
    console.warn(`[models/tracking] ${source}: response does not match schema`, result.error.issues);
  }
}

export const trackingApi = {
  usage: () =>
    api.get<TrackingUsageResponse>('/tracking/usage').then((response) => {
      checkContract(trackingUsageResponseSchema, response.data, 'GET /tracking/usage');
      return response;
    }),

  list: (params?: TrackingListParams) =>
    api.get<TrackedProductListResponse>('/tracking', { params }).then((response) => {
      checkContract(trackedProductListResponseSchema, response.data, 'GET /tracking');
      return response;
    }),

  create: (payload: TrackedProductCreateRequest) =>
    api.post<TrackedProductResponse>('/tracking', payload).then((response) => {
      checkContract(trackedProductResponseSchema, response.data, 'POST /tracking');
      return response;
    }),

  update: (trackedId: number, payload: TrackedProductUpdateRequest) =>
    api.patch<TrackedProductResponse>(`/tracking/${trackedId}`, payload).then((response) => {
      checkContract(trackedProductResponseSchema, response.data, `PATCH /tracking/${trackedId}`);
      return response;
    }),

  remove: (trackedId: number) => api.delete<void>(`/tracking/${trackedId}`),
};
