import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, within } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from 'vitest';

import { server } from '@/test/msw/server';
import { ThemeProvider } from '@/shared/providers/ThemeProvider';
import NotFoundPage from './not-found';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => '/',
}));

beforeAll(() =>
  server.listen({
    onUnhandledRequest: 'error',
    handlers: [
      http.get('*/api/users/me', () => HttpResponse.json({ detail: '401' }, { status: 401 })),
      http.get('*/api/notifications/unread-count', () => HttpResponse.json({ count: 0 })),
    ],
  }),
);
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  return render(
    <QueryClientProvider client={client}>
      <ThemeProvider>
        <NotFoundPage />
      </ThemeProvider>
    </QueryClientProvider>,
  );
}

describe('NotFoundPage', () => {
  it('explains the 404 instead of showing the default Next page', () => {
    renderPage();

    expect(
      screen.getByRole('heading', { level: 1, name: 'Страница не найдена' }),
    ).toBeInTheDocument();
    expect(screen.getByText('Ошибка 404')).toBeInTheDocument();
  });

  it('offers ways out of the dead end', () => {
    const { container } = renderPage();
    // Ссылки есть и в Header/Footer («Тарифы»), поэтому ищем только в main.
    const main = within(container.querySelector('main') as HTMLElement);

    expect(main.getByRole('link', { name: 'К поиску' })).toHaveAttribute('href', '/search');
    expect(main.getByRole('link', { name: 'Тарифы' })).toHaveAttribute('href', '/tariffs');
    expect(main.getByRole('link', { name: 'На главную' })).toHaveAttribute('href', '/');
  });

  it('uses the site design tokens rather than hardcoded colours', () => {
    const { container } = renderPage();
    const main = container.querySelector('main');

    expect(main?.className).toContain('bg-ivory');
  });
});
