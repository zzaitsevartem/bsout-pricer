import { api } from '@/shared/api/axios';
import type {
  AdminStatsResponse,
  BroadcastCreateRequest,
  BroadcastListResponse,
  BroadcastPreviewResponse,
  BroadcastRecipientListResponse,
  BroadcastResponse,
  BroadcastSendTestResponse,
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

  toggleUserAdmin: (id: number) =>
    api.post<UserBriefResponse>(`/admin/users/${id}/toggle-admin`),

  deleteUser: (id: number) => api.delete<void>(`/admin/users/${id}`),

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

  getBroadcasts: (page = 1, perPage = 10) =>
    api.get<BroadcastListResponse>('/admin/broadcasts', { params: { page, per_page: perPage } }),

  previewBroadcast: (data: BroadcastCreateRequest) =>
    api.post<BroadcastPreviewResponse>('/admin/broadcasts/preview', data),

  createBroadcast: (data: BroadcastCreateRequest) =>
    api.post<BroadcastResponse>('/admin/broadcasts', data),

  getBroadcast: (id: number) => api.get<BroadcastResponse>(`/admin/broadcasts/${id}`),

  getBroadcastRecipients: (
    id: number,
    status?: string,
    page = 1,
    perPage = 20,
  ) =>
    api.get<BroadcastRecipientListResponse>(`/admin/broadcasts/${id}/recipients`, {
      params: { status, page, per_page: perPage },
    }),

  sendBroadcastTest: (id: number, email?: string) =>
    api.post<BroadcastSendTestResponse>(`/admin/broadcasts/${id}/send-test`, { email }),

  launchBroadcast: (id: number) => api.post<BroadcastResponse>(`/admin/broadcasts/${id}/launch`),

  cancelBroadcast: (id: number) => api.post<BroadcastResponse>(`/admin/broadcasts/${id}/cancel`),

  deleteBroadcast: (id: number) => api.delete<void>(`/admin/broadcasts/${id}`),
};
