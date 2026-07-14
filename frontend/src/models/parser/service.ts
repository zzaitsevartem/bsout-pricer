import { api } from '@/shared/api/axios';
import type { ParserRunRequest, ParserStatusResponse } from './schema';

export const parserApi = {
  list: () =>
    api.get<ParserStatusResponse[]>('/admin/parsers'),

  run: (data: ParserRunRequest) =>
    api.post('/admin/parsers/run', data),
};
