import { api } from '@/shared/api/axios';
import type { ParserRunRequest, ParserRunResponse, ParserStatusResponse } from './schema';

export const parserApi = {
  list: () => api.get<ParserStatusResponse[]>('/admin/parsers'),

  run: (data: ParserRunRequest) => api.post<ParserRunResponse>('/admin/parsers/run', data),
};
