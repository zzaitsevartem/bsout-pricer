import axios from 'axios';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { trackingApi } from './service';
import { SUBSCRIPTION_REQUIRED_CODE, trackingLimitDetailSchema } from './schema';
import type {
  TrackedProductCreateRequest,
  TrackedProductResponse,
  TrackedProductUpdateRequest,
  TrackingListParams,
} from './schema';

const ALL_PAGE_SIZE = 100;
const ALL_PAGE_CAP = 5;

export const trackingKeys = {
  all: ['tracking'] as const,
  usage: ['tracking', 'usage'] as const,
  list: (params?: TrackingListParams) => ['tracking', 'list', params ?? null] as const,
  everything: ['tracking', 'everything'] as const,
};

export type TrackingGate =
  | { kind: 'limit'; message: string; used: number; limit: number }
  | { kind: 'subscription'; message: string }
  | { kind: 'other'; message: string };

const LIMIT_FALLBACK = 'Достигнут лимит отслеживаемых товаров по вашему тарифу.';
const SUBSCRIPTION_FALLBACK =
  'Требуется активная подписка. Оформите тариф, чтобы отслеживать товары.';
const OTHER_FALLBACK = 'Не удалось выполнить действие. Попробуйте ещё раз.';

function detailOf(error: unknown): unknown {
  if (!axios.isAxiosError(error)) {
    return undefined;
  }
  return (error.response?.data as { detail?: unknown } | undefined)?.detail;
}

export function trackingGate(error: unknown): TrackingGate | null {
  if (!axios.isAxiosError(error)) {
    return null;
  }

  const status = error.response?.status;
  const detail = detailOf(error);

  if (status === 402) {
    const parsed = trackingLimitDetailSchema.safeParse(detail);
    if (parsed.success) {
      return {
        kind: 'limit',
        message: parsed.data.message,
        used: parsed.data.used,
        limit: parsed.data.limit,
      };
    }
    return { kind: 'limit', message: LIMIT_FALLBACK, used: 0, limit: 0 };
  }

  if (status === 403) {
    const code = (detail as { code?: unknown } | undefined)?.code;
    const message = (detail as { message?: unknown } | undefined)?.message;
    return {
      kind: code === SUBSCRIPTION_REQUIRED_CODE ? 'subscription' : 'other',
      message: typeof message === 'string' && message.length > 0 ? message : SUBSCRIPTION_FALLBACK,
    };
  }

  if (status === undefined) {
    return null;
  }

  const message = (detail as { message?: unknown } | undefined)?.message;
  return {
    kind: 'other',
    message: typeof message === 'string' && message.length > 0 ? message : OTHER_FALLBACK,
  };
}

export function isTrackingGateStatus(error: unknown): boolean {
  const status = axios.isAxiosError(error) ? error.response?.status : undefined;
  return status === 402 || status === 403;
}

export function useTrackingUsage(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: trackingKeys.usage,
    queryFn: () => trackingApi.usage().then((r) => r.data),
    enabled: options?.enabled ?? true,
    retry: false,
  });
}

export function useTrackedProducts(params?: TrackingListParams, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: trackingKeys.list(params),
    queryFn: () => trackingApi.list(params).then((r) => r.data),
    enabled: options?.enabled ?? true,
    retry: false,
  });
}

async function fetchEveryTrackedProduct(): Promise<TrackedProductResponse[]> {
  const collected: TrackedProductResponse[] = [];
  for (let page = 1; page <= ALL_PAGE_CAP; page += 1) {
    const data = await trackingApi.list({ page, per_page: ALL_PAGE_SIZE }).then((r) => r.data);
    collected.push(...data.results);
    if (collected.length >= data.total || data.results.length === 0) {
      break;
    }
  }
  return collected;
}

export function useEveryTrackedProduct(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: trackingKeys.everything,
    queryFn: fetchEveryTrackedProduct,
    enabled: options?.enabled ?? true,
    retry: false,
  });
}

export function useTrackProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TrackedProductCreateRequest) =>
      trackingApi.create(payload).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trackingKeys.all });
    },
  });
}

export function useUpdateTrackedProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ trackedId, ...payload }: TrackedProductUpdateRequest & { trackedId: number }) =>
      trackingApi.update(trackedId, payload).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trackingKeys.all });
    },
  });
}

export function useUntrackProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (trackedId: number) => trackingApi.remove(trackedId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trackingKeys.all });
    },
  });
}
