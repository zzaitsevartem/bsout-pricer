import { api } from '@/shared/api/axios';
import { deviceSchema } from './schema';
export const deviceApi = {
  get: (key: string, signal?: AbortSignal) =>
    api
      .get(`/devices/${encodeURIComponent(key)}`, { signal })
      .then(({ data }) => deviceSchema.parse(data)),
};
