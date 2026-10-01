import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest';

import { server } from './msw/server';

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('msw wiring', () => {
  it('intercepts a mocked GET request', async () => {
    const res = await fetch('https://api.test/health');
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ status: 'ok' });
  });
});
