import { afterEach, describe, expect, it, vi } from 'vitest';

async function loadSitemap(url?: string) {
  vi.resetModules();
  if (url !== undefined) {
    vi.stubEnv('FRONTEND_BASE_URL', url);
  }
  const mod = await import('./sitemap');
  return mod.default();
}

describe('sitemap', () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('lists only public pages as absolute urls', async () => {
    const entries = await loadSitemap('https://bscout.ru');
    const paths = entries.map((entry) => new URL(entry.url).pathname);

    expect(paths).toEqual(
      expect.arrayContaining(['/', '/search', '/tariffs', '/contacts', '/faq', '/privacy', '/terms']),
    );
    for (const entry of entries) {
      expect(entry.url.startsWith('https://bscout.ru')).toBe(true);
    }
  });

  it('keeps authenticated and private routes out of the map', async () => {
    const entries = await loadSitemap('https://bscout.ru');
    const paths = entries.map((entry) => new URL(entry.url).pathname);

    for (const forbidden of ['/account', '/admin', '/subscription', '/api', '/login', '/register']) {
      expect(paths).not.toContain(forbidden);
    }
  });

  it('gives the home page the highest priority', async () => {
    const entries = await loadSitemap('https://bscout.ru');
    const home = entries.find((entry) => new URL(entry.url).pathname === '/');

    expect(home?.priority).toBe(1);
  });

  it('does not emit relative urls', async () => {
    const entries = await loadSitemap();

    for (const entry of entries) {
      expect(() => new URL(entry.url)).not.toThrow();
    }
  });
});
