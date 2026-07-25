import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminApi } from './service';
import type { MatchCandidateListParams, OfferImportItem, OfferLinkRequest } from './schema';

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
