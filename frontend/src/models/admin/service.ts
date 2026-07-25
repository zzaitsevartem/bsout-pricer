import { api } from '@/shared/api/axios';
import type {
  AdminStatsResponse,
  CandidateDecisionResponse,
  MatchCandidateListParams,
  MatchCandidateListResponse,
  OfferImportItem,
  OfferImportResponse,
  OfferLinkRequest,
  OfferLinkResponse,
  UserBriefResponse,
} from './schema';

export const adminApi = {
  getStats: () => api.get<AdminStatsResponse>('/admin/stats'),

  getUsers: (skip = 0, limit = 50) =>
    api.get<UserBriefResponse[]>('/admin/users', { params: { skip, limit } }),

  getUserById: (id: number) => api.get<UserBriefResponse>(`/admin/users/${id}`),

  toggleUserActive: (id: number) =>
    api.post<UserBriefResponse>(`/admin/users/${id}/toggle-active`),

  importOffers: (rows: OfferImportItem[]) =>
    api.post<OfferImportResponse>('/admin/offers/import', rows),

  getMatchCandidates: (params: MatchCandidateListParams = {}) =>
    api.get<MatchCandidateListResponse>('/admin/match-candidates', { params }),

  approveMatchCandidate: (candidateId: number) =>
    api.post<CandidateDecisionResponse>(`/admin/match-candidates/${candidateId}/approve`),

  rejectMatchCandidate: (candidateId: number) =>
    api.post<CandidateDecisionResponse>(`/admin/match-candidates/${candidateId}/reject`),

  linkOffer: (offerId: number, data: OfferLinkRequest) =>
    api.post<OfferLinkResponse>(`/admin/offers/${offerId}/link`, data),

  unlinkOffer: (offerId: number) => api.post<OfferLinkResponse>(`/admin/offers/${offerId}/unlink`),
};
