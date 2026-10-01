import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('https://api.test/health', () => HttpResponse.json({ status: 'ok' })),
];
