import { useMutation } from '@tanstack/react-query';
import { feedbackApi } from './service';
import type { FeedbackRequest } from './schema';

export function useSendFeedback() {
  return useMutation({
    mutationFn: (data: FeedbackRequest) => feedbackApi.send(data),
  });
}
