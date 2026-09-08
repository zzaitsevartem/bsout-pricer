import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminApi } from './service';
import type {
  BroadcastCreateRequest,
  BroadcastListResponse,
  BroadcastRecipientListResponse,
  MatchCandidateListParams,
  OfferImportItem,
  OfferLinkRequest,
} from './schema';

function hasActiveBroadcast(list?: BroadcastListResponse): boolean {
  return (
    list?.items.some(
      (broadcast) => broadcast.status === 'running' || broadcast.status === 'queued',
    ) ?? false
  );
}

export function useAdminStats() {
  return useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: () => adminApi.getStats().then((r) => r.data),
  });
}

export function useAdminUsers(skip = 0, limit = 50) {
  return useQuery({
    queryKey: ['admin', 'users', skip, limit],
    queryFn: () => adminApi.getUsers(skip, limit).then((r) => r.data),
  });
}

export function useAdminUser(id: number) {
  return useQuery({
    queryKey: ['admin', 'user', id],
    queryFn: () => adminApi.getUserById(id).then((r) => r.data),
    enabled: !!id,
  });
}

export function useToggleUserActive() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => adminApi.toggleUserActive(id).then((r) => r.data),
    onSuccess: (user) => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'user', user.id] });
    },
  });
}

export function useToggleUserAdmin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => adminApi.toggleUserAdmin(id).then((r) => r.data),
    onSuccess: (user) => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'user', user.id] });
    },
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => adminApi.deleteUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'stats'] });
    },
  });
}

export function useImportOffers() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (rows: OfferImportItem[]) => adminApi.importOffers(rows).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'stats'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'match-candidates'] });
    },
  });
}

export function useMatchCandidates(params: MatchCandidateListParams = {}) {
  return useQuery({
    queryKey: ['admin', 'match-candidates', params],
    queryFn: () => adminApi.getMatchCandidates(params).then((r) => r.data),
  });
}

export function useApproveMatchCandidate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (candidateId: number) =>
      adminApi.approveMatchCandidate(candidateId).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'match-candidates'] });
    },
  });
}

export function useRejectMatchCandidate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (candidateId: number) =>
      adminApi.rejectMatchCandidate(candidateId).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'match-candidates'] });
    },
  });
}

export function useLinkOffer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ offerId, data }: { offerId: number; data: OfferLinkRequest }) =>
      adminApi.linkOffer(offerId, data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'match-candidates'] });
    },
  });
}

export function useUnlinkOffer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (offerId: number) => adminApi.unlinkOffer(offerId).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'match-candidates'] });
    },
  });
}

export function useBroadcasts(page = 1, perPage = 10) {
  return useQuery({
    queryKey: ['admin', 'broadcasts', page, perPage],
    queryFn: () => adminApi.getBroadcasts(page, perPage).then((r) => r.data),
    refetchInterval: (query) => (hasActiveBroadcast(query.state.data) ? 3000 : false),
  });
}

export function useBroadcastRecipients(id: number, status?: string, page = 1, perPage = 20) {
  return useQuery({
    queryKey: ['admin', 'broadcasts', id, 'recipients', status, page, perPage],
    queryFn: () => adminApi.getBroadcastRecipients(id, status, page, perPage).then((r) => r.data),
    enabled: !!id,
    refetchInterval: 3000,
  });
}

function useBroadcastListCache() {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ['admin', 'broadcasts'] });
  };
}

export function useCreateBroadcast() {
  const invalidate = useBroadcastListCache();

  return useMutation({
    mutationFn: (data: BroadcastCreateRequest) =>
      adminApi.createBroadcast(data).then((r) => r.data),
    onSuccess: invalidate,
  });
}

export function useLaunchBroadcast() {
  const invalidate = useBroadcastListCache();

  return useMutation({
    mutationFn: (id: number) => adminApi.launchBroadcast(id).then((r) => r.data),
    onSuccess: invalidate,
  });
}

export function useCancelBroadcast() {
  const invalidate = useBroadcastListCache();

  return useMutation({
    mutationFn: (id: number) => adminApi.cancelBroadcast(id).then((r) => r.data),
    onSuccess: invalidate,
  });
}

export function useDeleteBroadcast() {
  const invalidate = useBroadcastListCache();

  return useMutation({
    mutationFn: (id: number) => adminApi.deleteBroadcast(id),
    onSuccess: invalidate,
  });
}

export function useSendBroadcastTest() {
  return useMutation({
    mutationFn: ({ id, email }: { id: number; email?: string }) =>
      adminApi.sendBroadcastTest(id, email).then((r) => r.data),
  });
}

export function usePreviewBroadcast() {
  return useMutation({
    mutationFn: (data: BroadcastCreateRequest) =>
      adminApi.previewBroadcast(data).then((r) => r.data),
  });
}
