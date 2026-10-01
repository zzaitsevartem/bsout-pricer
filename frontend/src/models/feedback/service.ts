import { api } from '@/shared/api/axios';
import type { FeedbackRequest, FeedbackResponse } from './schema';

export const feedbackApi = {
  send: (data: FeedbackRequest) => api.post<FeedbackResponse>('/feedback', data),
};
