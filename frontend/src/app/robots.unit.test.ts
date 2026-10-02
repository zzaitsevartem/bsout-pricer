import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

async function loadRobots(url?: string) {
  vi.resetModules();
  if (url !== undefined) {
    vi.stubEnv('FRONTEND_BASE_URL', url);
  }
  const mod = await import('./robots');
  return mod.default();
}

describe('robots', () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('indexes the site and keeps private sections out', async () => {
    const robots = await loadRobots();

    expect(robots.rules).toHaveLength(1);
    const rule = robots.rules[0];
    expect(rule.userAgent).toBe('*');
    expect(rule.allow).toBe('/');
    expect(rule.disallow).toEqual(
      expect.arrayContaining(['/account', '/admin', '/api/', '/subscription']),
    );
  });

  it('points at the sitemap on the configured host', async () => {
    const robots = await loadRobots('https://bscout.ru');

    expect(robots.sitemap).toBe('https://bscout.ru/sitemap.xml');
    expect(robots.host).toBe('https://bscout.ru');
  });

  it('falls back to localhost when the host is not configured', async () => {
    vi.resetModules();
    vi.stubEnv('FRONTEND_BASE_URL', '');
    const mod = await import('./robots');

    expect(mod.default().host).toBe('http://localhost:3000');
  });
});
